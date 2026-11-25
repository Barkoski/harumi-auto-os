#!/usr/bin/env python3
"""Harumi Auto OS para Linux (Orange Pi 5): servidor local da interface.

Faz no Linux o papel que o MainActivity + MapNetworkGateway fazem no Android:
  * serve a interface (pasta assets) em http://127.0.0.1:8765/assets/index.html;
  * responde a /assets/map-api/* (tiles vetoriais, glifos, tiles PNG, rota e busca),
    Internet primeiro e arquivo local do Brasil como reserva (mesma politica do app);
  * substitui a ponte HarumiNative (window.HarumiNative.dispatch) por POST /bridge.

So biblioteca padrao do Python (sem pip). Escuta apenas em 127.0.0.1.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import queue
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harumi_assistant import Assistant  # noqa: E402
import harumi_system  # noqa: E402
import harumi_store  # noqa: E402,F401  (os plugins o importam; aqui garante o mesmo modulo)

VERSION = "linux-0.3"
HOST, PORT = "127.0.0.1", int(os.environ.get("HARUMI_PORT", "8765"))
BASE = Path(os.environ.get("HARUMI_HOME", Path(__file__).resolve().parent))
ASSETS = Path(os.environ.get("HARUMI_ASSETS", BASE / "assets"))
SHIM = BASE / "linux-bridge.js"
DATA = Path(os.environ.get("HARUMI_DATA", Path.home() / ".local/share/harumi"))
MAPAS = DATA / "mapas"
CACHE = Path(os.environ.get("HARUMI_CACHE", Path.home() / ".cache/harumi/maps"))
USER_AGENT = f"HarumiAutoOS/{VERSION} (Orange Pi; personal navigation prototype)"
DAY = 86400
ROUTE_TTL = 300
MAX_QUERY = 120
OFM_HOST = "https://tiles.openfreemap.org/"
OFM_TILEJSON = OFM_HOST + "planet"

MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
        ".map": "application/json", ".css": "text/css; charset=utf-8",
        ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
        ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".mp3": "audio/mpeg", ".wav": "audio/wav",
        ".ogg": "audio/ogg", ".webp": "image/webp", ".ico": "image/x-icon", ".pbf": "application/x-protobuf", ".txt": "text/plain"}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, file=sys.stderr, flush=True)


# ------------------------------------------------------------------ rede e cache

_pace_lock = threading.Lock()
_last_provider = 0.0


def pace():
    """Nominatim/OSRM publicos: no maximo ~1 pedido por segundo."""
    global _last_provider
    with _pace_lock:
        wait = 1.1 - (time.time() - _last_provider)
        if wait > 0:
            time.sleep(wait)
        _last_provider = time.time()


def download(url: str, limit: int, timeout: float = 12.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise OSError(f"provider status {r.status}")
        data = r.read(limit + 1)
        if len(data) > limit:
            raise OSError("response too large")
        return data


def gunzip_if_needed(data: bytes, limit: int) -> bytes:
    if len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B:
        out = gzip.decompress(data)
        if len(out) > limit:
            raise OSError("response too large")
        return out
    return data


def cache_file(key: str) -> Path:
    return CACHE / hashlib.sha256(key.encode()).hexdigest()


def cache_read(key: str, ttl: float):
    f = cache_file(key)
    try:
        st = f.stat()
    except OSError:
        return None, 0.0
    if time.time() - st.st_mtime >= ttl:
        return None, st.st_mtime
    try:
        return f.read_bytes(), st.st_mtime
    except OSError:
        return None, 0.0


def cache_stale(key: str):
    f = cache_file(key)
    try:
        return f.read_bytes(), f.stat().st_mtime
    except OSError:
        return None, 0.0


def cache_write(key: str, data: bytes):
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        f = cache_file(key)
        tmp = f.with_suffix(".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, f)
        prune_async()
    except OSError:
        pass


_prune_lock = threading.Lock()


def prune_async():
    if not _prune_lock.acquire(blocking=False):
        return

    def run():
        try:
            files = [p for p in CACHE.iterdir() if p.is_file() and not p.name.endswith(".tmp")]
            total = sum(p.stat().st_size for p in files)
            if total < 256 * 1024 * 1024:
                return
            for p in sorted(files, key=lambda p: p.stat().st_mtime):
                size = p.stat().st_size
                p.unlink(missing_ok=True)
                total -= size
                if total < 192 * 1024 * 1024:
                    break
        except OSError:
            pass
        finally:
            _prune_lock.release()

    threading.Thread(target=run, daemon=True).start()


# ------------------------------------------------------------------ MBTiles do Brasil

class OfflineTiles:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.db = None
        self.bounds = None
        self.last_try = 0.0

    def _open(self):
        if self.db is not None:
            return self.db
        if time.time() - self.last_try < 30 and self.last_try:
            return None
        self.last_try = time.time()
        if not self.path.is_file():
            return None
        try:
            db = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, check_same_thread=False)
            meta = dict(db.execute("SELECT name, value FROM metadata").fetchall())
            if "bounds" in meta:
                self.bounds = [float(v) for v in meta["bounds"].split(",")]
            self.db = db
            log("offline mbtiles:", self.path, meta.get("name"), "bounds", meta.get("bounds"))
            return db
        except sqlite3.Error as e:
            log("mbtiles nao abre:", e)
            return None

    def lookup(self, z, x, y):
        with self.lock:
            db = self._open()
            if db is None:
                return None, False
            try:
                row = db.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                                 (z, x, (1 << z) - 1 - y)).fetchone()
                return (row[0] if row else None), False
            except sqlite3.Error:
                return None, True

    def covers_missing(self, z, x, y) -> bool:
        """Tile inteiro dentro dos limites do arquivo: ausente = vazio de verdade (mar, por exemplo)."""
        if not self.bounds:
            return False
        n = 1 << z
        west = x / n * 360 - 180
        east = (x + 1) / n * 360 - 180

        def lat(t):
            return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * t / n))))
        north, south = lat(y), lat(y + 1)
        w, s, e, nn = self.bounds
        return west >= w and east <= e and south >= s and north <= nn


# ------------------------------------------------------------------ busca offline (porta fiel do OfflineSearch.java)

STOPWORDS = {"de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos", "e"}
UFS = {"ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb", "pr", "pe", "pi", "rj",
       "rn", "rs", "ro", "rr", "sc", "sp", "se", "to"}
CANDIDATE_CAP = 3000


def normalize(s: str | None) -> str:
    if not s:
        return ""
    d = unicodedata.normalize("NFD", s.lower())
    out, space = [], True
    for c in d:
        if "a" <= c <= "z" or "0" <= c <= "9":
            out.append(c)
            space = False
        elif unicodedata.category(c) == "Mn":
            continue
        elif not space:
            out.append(" ")
            space = True
    return "".join(out).rstrip(" ")


def tokens(q):
    n = normalize(q)
    return [t for t in n.split(" ") if t and t not in STOPWORDS] if n else []


def build_match(city_tokens, terms):
    parts = [f"city:{c}" for c in (city_tokens or [])]
    for i, t in enumerate(terms):
        parts.append(t + ("*" if i == len(terms) - 1 else ""))
    return " ".join(parts)


def all_prefixes(terms, name_norm):
    words = name_norm.split(" ")
    return all(any(w.startswith(t) for w in words) for t in terms)


def score(qn, terms, name_norm, rank, dist):
    s = rank * 0.5
    if name_norm == qn:
        s += 40
    elif name_norm.startswith(qn):
        s += 25
    elif all_prefixes(terms, name_norm):
        s += 10
    if dist is not None:
        s += 40.0 / (1.0 + dist / 15.0)
    return s


def dist_km(lat1, lon1, lat2, lon2):
    dy = (lat1 - lat2) * 111.0
    dx = (lon1 - lon2) * 111.0 * math.cos(math.radians(lat1))
    return math.hypot(dx, dy)


def display_name(name, kind, city, uf):
    hc, hu = bool(city), bool(uf)
    if kind == "estado":
        return name
    if kind == "cidade":
        return f"{name} - {uf}" if hu else name
    if kind in ("rua", "rodovia", "praça"):
        return name if not hc else f"{name}, {city}" + (f" - {uf}" if hu else "")
    return name if not hc else f"{name} — {city}" + (f", {uf}" if hu else "")


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def fuel_stops(search, route, every_km=150.0, radius_km=6.0):
    """Postos do indice offline perto da rota, a cada ~every_km. Lista vazia se a rota for curta ou sem indice."""
    if not route or route.get("distance", 0) < every_km * 1000 * 1.3:
        return []
    coords, out, acc, target = route["coords"], [], 0.0, every_km
    with search.lock:
        db = search._open()
        if db is None:
            return []
        for i in range(1, len(coords)):
            (lo1, la1), (lo2, la2) = coords[i - 1][:2], coords[i][:2]
            acc += haversine_km(la1, lo1, la2, lo2)
            if acc < target:
                continue
            d = radius_km / 111.0
            best = None
            for name, city, uf, la, lo in db.execute(
                    "SELECT name, city, uf, lat, lon FROM places WHERE kind='posto' AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
                    (la2 - d, la2 + d, lo2 - d / max(0.2, math.cos(math.radians(la2))), lo2 + d / max(0.2, math.cos(math.radians(la2))))):
                k = haversine_km(la2, lo2, la, lo)
                if k <= radius_km and (best is None or k < best[0]):
                    best = (k, name, city, uf, la, lo)
            if best:
                out.append({"km": round(acc), "name": best[1], "city": best[2] or "", "uf": best[3] or "",
                            "lat": best[4], "lon": best[5], "offRouteKm": round(best[0], 1)})
            target += every_km
    return out


class OfflineSearch:
    SELECT = ("SELECT p.id,p.name,p.kind,p.city,p.uf,p.lat,p.lon,p.rank,p.norm FROM places p "
              f"WHERE p.id IN (SELECT docid FROM busca WHERE busca MATCH ? LIMIT {CANDIDATE_CAP})")

    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.db = None
        self.last_try = 0.0

    def _open(self):
        if self.db is not None:
            return self.db
        if self.last_try and time.time() - self.last_try < 30:
            return None
        self.last_try = time.time()
        if not self.path.is_file():
            return None
        try:
            self.db = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, check_same_thread=False)
            return self.db
        except sqlite3.Error as e:
            log("indice de busca nao abre:", e)
            return None

    def search_json(self, q, lat, lon, limit=5):
        try:
            with self.lock:
                db = self._open()
                if db is None:
                    return None
                rows = self._search(db, q, lat, lon, max(1, limit))
                return json.dumps([{"name": display_name(r["name"], r["kind"], r["city"], r["uf"]),
                                    "lat": r["lat"], "lon": r["lon"]} for r in rows], ensure_ascii=False)
        except Exception as e:  # qualquer falha: o chamador cai para a Internet
            log("busca offline falhou:", e)
            return None

    def _search(self, db, q, lat, lon, limit):
        toks = tokens(q)
        if not toks:
            return []
        uf_filter = None
        if len(toks) > 1 and toks[-1] in UFS:
            uf_filter, toks = toks[-1], toks[:-1]
        merged: dict[int, dict] = {}
        filtered = False
        for k in range(min(3, len(toks) - 1), 0, -1):
            suf = toks[-k:]
            cities = self._city_lookup(db, " ".join(suf), uf_filter)
            if not cities:
                continue
            terms = toks[:-k]
            self._collect(db, build_match(suf, terms), terms, cities, lat, lon, merged)
            if merged:
                filtered = True
                break
        if not filtered:
            if lat is not None and lon is not None:
                near = self._nearest_city(db, lat, lon)
                if near:
                    self._collect(db, build_match(near[0].split(" "), toks), toks, [near], lat, lon, merged)
            self._collect(db, build_match(None, toks), toks, None, lat, lon, merged)
        out = list(merged.values())
        if uf_filter:
            keep = [r for r in out if (r["uf"] or "").lower() == uf_filter]
            if keep:
                out = keep
        out.sort(key=lambda r: r["score"], reverse=True)
        return out[:limit]

    @staticmethod
    def _city_lookup(db, norm_name, uf):
        res = []
        for norm, u in db.execute("SELECT norm, uf FROM places WHERE kind='cidade' AND norm=?", (norm_name,)):
            u = (u or "").lower()
            if uf is None or uf == u:
                res.append((norm, u))
        return res

    @staticmethod
    def _nearest_city(db, lat, lon):
        best, bd = None, float("inf")
        for norm, uf, la, lo in db.execute(
                "SELECT norm, uf, lat, lon FROM places WHERE kind='cidade' AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
                (lat - 0.6, lat + 0.6, lon - 0.6, lon + 0.6)):
            d = dist_km(lat, lon, la, lo)
            if d < bd:
                bd, best = d, (norm, (uf or "").lower())
        return best

    def _collect(self, db, match, terms, city_filter, lat, lon, into):
        if not match or not terms:
            return
        qn = " ".join(terms)
        for pid, name, kind, city, uf, la, lo, rank, norm in db.execute(self.SELECT, (match,)):
            if pid in into:
                continue
            if city_filter is not None:
                cn, u = normalize(city), (uf or "").lower()
                if not any(cf[0] == cn and cf[1] == u for cf in city_filter):
                    continue
            d = dist_km(lat, lon, la, lo) if lat is not None and lon is not None else None
            into[pid] = {"name": name, "kind": kind, "city": city, "uf": uf, "lat": la, "lon": lo,
                         "score": score(qn, terms, norm or "", rank or 0, d)}


# ------------------------------------------------------------------ validacoes (iguais ao app Android)

def validate_query(q):
    if q is None:
        raise ValueError("missing q")
    t = q.strip()
    if not t or len(t) > MAX_QUERY or "http" in t.lower() or any(unicodedata.category(c) == "Cc" for c in t):
        raise ValueError("invalid q")
    return t


def parse_coord(v, lo, hi):
    if v is None or len(v) > 20 or not re.fullmatch(r"-?[0-9]+(\.[0-9]+)?", v):
        return None
    d = float(v)
    return d if lo <= d <= hi else None


def route_points(points):
    """'lon,lat,lon,lat' (dois pontos, dentro do Brasil) -> caminho OSRM. Igual ao RouteCoordinates.java."""
    if not points or len(points) > 100 or not re.fullmatch(r"[-0-9.,]+", points):
        raise ValueError("points")
    vals = points.split(",")
    if len(vals) != 4:
        raise ValueError("points")
    p = [float(v) for v in vals]
    for i, v in enumerate(p):
        lo, hi = (-75, -30) if i % 2 == 0 else (-35, 6)
        if not math.isfinite(v) or v < lo or v > hi:
            raise ValueError("points")
    return f"{p[0]:.6f},{p[1]:.6f};{p[2]:.6f},{p[3]:.6f}"


def parse_bearing(v):
    if v is None or not re.fullmatch(r"[0-9]{1,3}", v):
        return None
    b = int(v)
    return b if b <= 359 else None


def normalize_geocode(raw: bytes) -> str:
    out = []
    for o in json.loads(raw):
        if not isinstance(o, dict):
            continue
        name, la, lo = o.get("display_name"), o.get("lat"), o.get("lon")
        try:
            la, lo = float(la), float(lo)
        except (TypeError, ValueError):
            continue
        if not isinstance(name, str) or not name.strip() or abs(la) > 90 or abs(lo) > 180:
            continue
        out.append({"name": name.strip()[:MAX_QUERY], "lat": round(la, 6), "lon": round(lo, 6)})
    return json.dumps(out, ensure_ascii=False)


def parse_tile_template(tile_json: bytes) -> str:
    t = json.loads(tile_json)["tiles"][0]
    if len(t) > 300 or ".." in t or not re.fullmatch(r"https://tiles\.openfreemap\.org/[A-Za-z0-9_./-]+/\{z\}/\{x\}/\{y\}\.pbf", t):
        raise OSError("untrusted tile template")
    return t


# ------------------------------------------------------------------ gateway map-api

class MapGateway:
    def __init__(self):
        self.tiles = OfflineTiles(MAPAS / "brasil.mbtiles")
        self.search = OfflineSearch(MAPAS / "busca-brasil.sqlite")
        self.force_offline = (MAPAS.parent / "forcar-offline").is_file()
        self.last_route = None
        if self.force_offline:
            log("forcar-offline ativo: rota e busca pulam a Internet")

    def template(self):
        data, _ = cache_read(OFM_TILEJSON, DAY)
        if data is None:
            try:
                data = gunzip_if_needed(download(OFM_TILEJSON, 256 * 1024, 6), 256 * 1024)
                cache_write(OFM_TILEJSON, data)
            except OSError:
                data, _ = cache_stale(OFM_TILEJSON)
                if data is None:
                    raise
        return parse_tile_template(data)

    def handle(self, sub: str, qs: dict):
        """Devolve (status, mime, bytes, max_age)."""
        q1 = lambda k: (qs.get(k) or [None])[0]
        m = re.fullmatch(r"vt/(\d{1,2})/(\d{1,6})/(\d{1,6})\.pbf", sub)
        if m:
            z, x, y = map(int, m.groups())
            if z > 14 or x >= (1 << z) or y >= (1 << z):
                raise ValueError("tile")
            return self.vector_tile(z, x, y)
        m = re.fullmatch(r"glyphs/([A-Za-z][A-Za-z ,]{0,79})/(\d{1,6}-\d{1,6})\.pbf", urllib.parse.unquote(sub))
        if m:
            url = OFM_HOST + "fonts/" + urllib.parse.quote(m.group(1)) + "/" + m.group(2) + ".pbf"
            return self.cached(url, 30 * DAY, "application/x-protobuf", 2 * 1024 * 1024, unzip=True)
        m = re.fullmatch(r"tiles/(\d{1,2})/(\d{1,6})/(\d{1,6})\.png", sub)
        if m:
            z, x, y = map(int, m.groups())
            if z < 3 or z > 18 or x >= (1 << z) or y >= (1 << z):
                raise ValueError("tile")
            return self.cached(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png", 7 * DAY, "image/png", 512 * 1024)
        if sub == "geocode":
            return self.geocode(q1("q"), q1("lat"), q1("lon"))
        if sub == "route":
            return self.route(q1("points"), parse_bearing(q1("bearing")))
        raise ValueError("unknown")

    def cached(self, url, ttl, mime, limit, unzip=False):
        data, _ = cache_read(url, ttl)
        if data is None:
            try:
                data = download(url, limit)
                if unzip:
                    data = gunzip_if_needed(data, limit)
                cache_write(url, data)
            except OSError:
                data, _ = cache_stale(url)
                if data is None:
                    raise
        return 200, mime, data, int(ttl)

    def vector_tile(self, z, x, y):
        try:
            url = self.template().replace("{z}", str(z)).replace("{x}", str(x)).replace("{y}", str(y))
            return self.cached(url, 30 * DAY, "application/x-protobuf", 2 * 1024 * 1024, unzip=True)
        except OSError:
            data, failed = self.tiles.lookup(z, x, y)
            if data is not None:
                return 200, "application/x-protobuf", gunzip_if_needed(data, 2 * 1024 * 1024), DAY
            if not failed and self.tiles.covers_missing(z, x, y):
                return 200, "application/x-protobuf", b"", DAY
            raise

    def geocode(self, q, lat, lon):
        t = validate_query(q)
        la, lo = parse_coord(lat, -35, 6), parse_coord(lon, -75, -30)
        url = "https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=br&limit=5&q=" + urllib.parse.quote_plus(t)
        if la is not None and lo is not None:
            url += f"&viewbox={lo - 0.5:.4f},{la + 0.5:.4f},{lo + 0.5:.4f},{la - 0.5:.4f}&bounded=0"
        data, _ = cache_read(url, 30 * DAY)
        if data is not None and not self.force_offline:
            return 200, "application/json", normalize_geocode(data).encode(), 30 * DAY
        try:
            if self.force_offline:
                raise OSError("forcar-offline")
            pace()
            data = download(url, 64 * 1024, 6.5)
            cache_write(url, data)
            return 200, "application/json", normalize_geocode(data).encode(), 30 * DAY
        except (OSError, ValueError):
            off = self.search.search_json(t, la, lo, 5)
            if off is not None:
                return 200, "application/json", off.encode(), 60
            stale, _ = cache_stale(url)
            if stale is not None:
                return 200, "application/json", normalize_geocode(stale).encode(), 60
            raise OSError("geocode unavailable")

    def route(self, points, bearing):
        path = route_points(points)
        url = ("https://router.project-osrm.org/route/v1/driving/" + path +
               "?steps=true&overview=full&geometries=geojson&alternatives=false")
        if bearing is not None:
            url += f"&bearings={bearing},45;"
        data, mtime = cache_read(url, ROUTE_TTL)
        cached = data is not None
        if data is None:
            try:
                if self.force_offline:
                    raise OSError("forcar-offline")
                pace()
                data = download(url, 2 * 1024 * 1024, 6.5)
                cache_write(url, data)
                mtime = time.time()
            except OSError:
                data, mtime = cache_stale(url)
                cached = True
                if data is None:
                    # Rota sem Internet (GraphHopper) entra na fase 2.
                    raise
        j = json.loads(data)
        try:
            r0 = j["routes"][0]
            self.last_route = {"coords": r0["geometry"]["coordinates"], "distance": r0.get("distance", 0), "duration": r0.get("duration", 0)}
        except (KeyError, IndexError, TypeError):
            pass
        j["cached"] = cached
        j["computedAt"] = int(mtime * 1000)
        return 200, "application/json", json.dumps(j).encode(), ROUTE_TTL


# ------------------------------------------------------------------ ponte HarumiNative

class EventHub:
    """Canal servidor -> pagina (Server-Sent Events). Cada evento e uma chamada {fn, args} que a ponte aplica."""

    def __init__(self):
        self.lock = threading.Lock()
        self.clients: list[queue.Queue] = []

    def subscribe(self):
        q = queue.Queue(maxsize=500)
        with self.lock:
            self.clients.append(q)
        return q

    def unsubscribe(self, q):
        with self.lock:
            if q in self.clients:
                self.clients.remove(q)

    def emit(self, fn, *args):
        msg = json.dumps({"fn": fn, "args": list(args)}, ensure_ascii=False)
        with self.lock:
            for q in self.clients:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass


class AppWindows:
    """Apps web (YouTube...) em janela propria do Chromium, por cima da Harumi, com botao para voltar."""

    APPS = {"youtube": "https://www.youtube.com/"}

    def __init__(self):
        self.proc = None

    def open(self, app_id):
        url = self.APPS.get(app_id)
        if not url:
            return False
        self.close()
        env = dict(os.environ)
        env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        env.setdefault("WAYLAND_DISPLAY", "wayland-0")
        cmd = ["/usr/bin/chromium", f"--app={url}", "--ozone-platform=wayland", "--start-fullscreen",
               f"--user-data-dir={Path.home() / '.config/harumi-apps'}", f"--load-extension={BASE / 'back-ext'}",
               "--no-first-run", "--noerrdialogs", "--disable-translate", "--password-store=basic",
               "--autoplay-policy=no-user-gesture-required", "--lang=pt-BR", "--accept-lang=pt-BR,pt"]
        if os.environ.get("HARUMI_APP_DEBUG") == "1":  # bancada: DevTools so em 127.0.0.1
            cmd += ["--remote-debugging-address=127.0.0.1", "--remote-debugging-port=9223"]
        self.proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=True)
        return True

    def close(self):
        p, self.proc = self.proc, None
        if p and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGTERM)
                p.wait(5)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except OSError:
                    pass


# ------------------------------------------------------------------ modulos (front) e plugins (back)
# Recursos novos entram soltando arquivos: linux/modules/*.js|css (injetados na pagina) e linux/plugins/*.py
# (rotas e acoes). Nomes com "_" no comeco so valem com HARUMI_PROBE=1 (sondas de teste).

MODULE_NAME = re.compile(r"[a-z0-9_-]+\.(js|css)")
PLUGIN_ROUTE = re.compile(r"/linux/[a-z0-9_-]{1,40}")
RESERVED_ROUTES = {"/linux/status", "/linux/fuel-stops", "/linux/close-app"}
PLUGIN_ROUTES: dict = {}
PLUGIN_POST_ROUTES: dict = {}
PLUGIN_ACTIONS: dict = {}


def _probe_on() -> bool:
    return os.environ.get("HARUMI_PROBE") == "1"


def module_files() -> list:
    """Nomes de linux/modules/*.js|css em ordem alfabetica (sondas "_" so com HARUMI_PROBE=1)."""
    d = BASE / "modules"
    if not d.is_dir():
        return []
    return sorted(f.name for f in d.iterdir()
                  if f.is_file() and MODULE_NAME.fullmatch(f.name) and (_probe_on() or not f.name.startswith("_")))


def modules_head() -> bytes:
    out = b""
    for n in module_files():
        out += (f'<script src="/modules/{n}" defer></script>' if n.endswith(".js")
                else f'<link rel="stylesheet" href="/modules/{n}">').encode()
    return out


def load_plugins(directory=None, bridge_allowed=None) -> list:
    """Importa linux/plugins/*.py. Erro em um plugin e registrado e ignorado. Devolve os nomes carregados."""
    import importlib.util
    d = Path(directory) if directory else BASE / "plugins"
    loaded = []
    if not d.is_dir():
        return loaded
    allowed = bridge_allowed or Bridge.ALLOWED
    for f in sorted(d.glob("*.py")):
        if f.name.startswith("_") and not _probe_on():
            continue
        try:
            spec = importlib.util.spec_from_file_location("harumi_plugin_" + re.sub(r"\W", "_", f.stem), f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for r, h in (getattr(mod, "ROUTES", None) or {}).items():
                if PLUGIN_ROUTE.fullmatch(str(r)) and r not in RESERVED_ROUTES and callable(h):
                    PLUGIN_ROUTES.setdefault(r, h)
                else:
                    log("plugin", f.name, "rota ignorada:", r)
            for r, h in (getattr(mod, "POST_ROUTES", None) or {}).items():
                if PLUGIN_ROUTE.fullmatch(str(r)) and r not in RESERVED_ROUTES and callable(h):
                    PLUGIN_POST_ROUTES.setdefault(r, h)
                else:
                    log("plugin", f.name, "rota POST ignorada:", r)
            for a, fn in (getattr(mod, "ACTIONS", None) or {}).items():
                if isinstance(a, str) and allowed.fullmatch(a) and callable(fn):
                    PLUGIN_ACTIONS.setdefault(a, fn)
                else:
                    log("plugin", f.name, "acao ignorada:", a)
            loaded.append(f.name)
        except Exception as e:  # plugin quebrado nao derruba o servidor
            log("plugin", f.name, "falhou ao carregar:", repr(e))
    return loaded


class Bridge:
    """Equivale ao Bridge/handle() do MainActivity. Respostas imediatas voltam na propria requisicao;
    as demoradas (IA) chegam depois pelo EventHub."""

    ALLOWED = re.compile(r"[a-z][a-z0-9_.]{0,40}")

    def __init__(self, hub: EventHub):
        self.hub = hub
        self.apps = AppWindows()
        self.assistant = Assistant(hub.emit, lambda: GATEWAY.last_route)

    def state(self):
        return {"NAV": "Navegação da Harumi", "MUSIC": "Spotify · dispositivo Harumi", "CAMERA360": "Câmeras",
                "device": "Orange Pi 5", "version": VERSION, "animation": "idle",
                "connectivity": "Rede do Orange Pi", "assistantStatus": "Pronta · Orange Pi", "assistantBusy": False,
                "diagnostics": "Diagnóstico do carro ainda não conectado", "wake": "off"}

    def dispatch(self, action: str, module: str):
        if (action != "__ready" and not self.ALLOWED.fullmatch(action or "")) or len(module or "") > (1600 if action == "assistant.ask" else 64):
            return []
        calls = []
        if action == "__ready":
            calls.append({"fn": "harumiUpdate", "args": [self.state()]})
        elif action == "catalog.list":
            calls.append({"fn": "harumiAppsUpdate", "args": [[
                {"id": "youtube", "installed": True, "status": "Abrir no Orange Pi"},
                {"id": "spotify", "installed": True, "status": "Dispositivo Harumi"}]]})
        elif action == "launcher.list":
            calls.append({"fn": "harumiLauncherUpdate", "args": [{"apps": [
                {"id": "youtube", "name": "YouTube", "icon": "/app-icon/youtube"},
                {"id": "spotify", "name": "Spotify", "icon": "/app-icon/spotify"}], "catalog": []}]})
        elif action in ("catalog.open", "launcher.open") and module in ("youtube", "spotify", "claude", "chatgpt", "browser", "waze"):
            calls.append({"fn": "harumiLinuxOpen", "args": [module]})  # a pagina decide: dentro da Harumi ou janela
        elif action == "assistant.ask":
            self.assistant.ask(module)
        elif action in ("assistant.cancel", "assistant.cancel.quiet"):
            self.assistant.cancel(action == "assistant.cancel")
        elif action == "voice.greet":
            self.assistant.ask("oi")
        elif action == "linux.open":
            if module == "spotify":
                calls.append({"fn": "__notify", "args": ["Spotify: escolha o dispositivo “Harumi” no app. A tela de música da Harumi chega com o Client ID."]})
            elif not self.apps.open(module):
                calls.append({"fn": "__notify", "args": ["App não disponível no Orange Pi."]})
        elif action == "linux.close":
            self.apps.close()
        elif action == "volume.step" and re.fullmatch(r"[+-]?\d{1,3}", module or ""):
            calls.append({"fn": "harumiVolume", "args": [harumi_system.step_volume(int(module))]})
        elif action == "volume.set" and re.fullmatch(r"\d{1,3}", module or ""):
            calls.append({"fn": "harumiVolume", "args": [harumi_system.set_volume(int(module))]})
        elif action == "volume.mute":
            calls.append({"fn": "harumiVolume", "args": [harumi_system.toggle_mute()]})
        elif action in PLUGIN_ACTIONS:
            try:
                calls.extend(PLUGIN_ACTIONS[action](module, self.hub.emit) or [])
            except Exception as e:  # plugin nao derruba a ponte
                log("plugin acao", action, repr(e))
                calls.append({"fn": "__notify", "args": ["Falha no recurso."]})
        else:
            calls.append({"fn": "__notify", "args": [f"Ainda não disponível no Orange Pi: {action}"]})
        return calls


# ------------------------------------------------------------------ HTTP

GATEWAY = MapGateway()
HUB = EventHub()
BRIDGE = Bridge(HUB)
PAGE_ORIGIN = f"http://127.0.0.1:{PORT}"


class Handler(BaseHTTPRequestHandler):
    server_version = "Harumi/" + VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if os.environ.get("HARUMI_VERBOSE"):
            log(self.address_string(), fmt % args)

    def send_bytes(self, status, mime, body: bytes, max_age=0):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", f"private, max-age={max_age}" if max_age else "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self.host_ok():
            return self.send_bytes(403, "text/plain", b"forbidden")
        u = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(u.path)
        if path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/assets/index.html")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path == "/linux-bridge.js":
            return self.send_bytes(200, MIME[".js"], SHIM.read_bytes())
        if path in ("/linux-embed.js", "/linux-embed.css", "/linux-layout.js", "/linux-layout.css", "/linux-extras.js", "/linux-keyboard.js", "/linux-mcu.js"):
            return self.send_bytes(200, MIME[Path(path).suffix], (BASE / path.lstrip("/")).read_bytes())
        if path == "/events":
            return self.events()
        m_mod = re.fullmatch(r"/modules/([a-z0-9_-]+\.(?:js|css))", path)
        if m_mod:
            if m_mod.group(1) not in module_files():
                return self.send_bytes(404, "text/plain", b"not found")
            return self.send_bytes(200, MIME[Path(path).suffix], (BASE / "modules" / m_mod.group(1)).read_bytes())
        if path in PLUGIN_ROUTES:
            query = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            try:
                status, mime, body = PLUGIN_ROUTES[path](query)
                return self.send_bytes(status, mime, body)
            except Exception as e:
                log("plugin rota", path, repr(e))
                return self.send_bytes(500, "application/json", b'{"ok":false}')
        m_icon = re.fullmatch(r"/app-icon/([a-z]{2,20})", path)
        if m_icon:
            for ext in ("png", "svg", "ico"):
                f = BASE / "app-icons" / f"{m_icon.group(1)}.{ext}"
                if f.is_file():
                    mime = {"png": "image/png", "svg": "image/svg+xml", "ico": "image/x-icon"}[ext]
                    return self.send_bytes(200, mime, f.read_bytes(), DAY)
            return self.send_bytes(404, "text/plain", b"sem icone")
        if path == "/linux/fuel-stops":
            stops = fuel_stops(GATEWAY.search, GATEWAY.last_route)
            return self.send_bytes(200, "application/json", json.dumps({"stops": stops}, ensure_ascii=False).encode())
        if path == "/linux/status":
            return self.send_bytes(200, "application/json", json.dumps(harumi_system.status(), ensure_ascii=False).encode())
        if path.startswith("/assets/map-api/"):
            try:
                status, mime, body, age = GATEWAY.handle(u.path[len("/assets/map-api/"):], urllib.parse.parse_qs(u.query))
                return self.send_bytes(status, mime, body, age)
            except ValueError:
                return self.send_bytes(400, "application/json", b'{"code":"BadRequest"}')
            except Exception as e:  # rede fora e sem reserva local
                if os.environ.get("HARUMI_VERBOSE"):
                    log("map-api", path, e)
                return self.send_bytes(503, "application/json", b'{"code":"Unavailable"}')
        if path.startswith("/assets/"):
            return self.static(path[len("/assets/"):])
        return self.send_bytes(404, "text/plain", b"not found")

    def static(self, rel):
        target = (ASSETS / rel).resolve()
        try:
            target.relative_to(ASSETS.resolve())
        except ValueError:
            return self.send_bytes(403, "text/plain", b"forbidden")
        if not target.is_file():
            return self.send_bytes(404, "text/plain", b"not found")
        body = target.read_bytes()
        if rel == "index.html":
            # A ponte do Linux entra antes de qualquer script da interface.
            body = body.replace(b"<head>", b'<head><script src="/linux-bridge.js"></script>'
                                b'<link rel="stylesheet" href="/linux-embed.css">'
                                b'<script src="/linux-embed.js" defer></script>'
                                b'<link rel="stylesheet" href="/linux-layout.css">'
                                b'<script src="/linux-layout.js" defer></script>'
                                b'<script src="/linux-extras.js" defer></script>'
                                b'<script src="/linux-keyboard.js" defer></script>'
                                b'<script src="/linux-mcu.js" defer></script>' + modules_head(), 1)
        return self.send_bytes(200, MIME.get(target.suffix.lower(), "application/octet-stream"), body)

    def events(self):
        """SSE: mantem a conexao aberta e repassa as chamadas emitidas pelo servidor (IA, comandos)."""
        q = HUB.subscribe()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.close_connection = True
            while True:
                try:
                    msg = q.get(timeout=15)
                    self.wfile.write(f"data: {msg}\n\n".encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            HUB.unsubscribe(q)

    def do_POST(self):
        # Fechar app (YouTube): so a extensao "Voltar a Harumi" (origem chrome-extension://, que pagina web nao forja).
        # Acao inofensiva (fecha a janela do app); um token em arquivo nao serve: o Chromium guarda o service worker antigo.
        if self.host_ok() and self.path == "/linux/close-app":
            if (self.headers.get("Origin") or "").startswith("chrome-extension://"):
                BRIDGE.apps.close()
                return self.send_bytes(200, "application/json", b"{}")
            return self.send_bytes(403, "text/plain", b"forbidden")
        origin = self.headers.get("Origin")
        if self.host_ok() and self.path in PLUGIN_POST_ROUTES and not (origin and origin != PAGE_ORIGIN):
            try:
                n = int(self.headers.get("Content-Length") or 0)
                if n > 65536:
                    raise ValueError
                data = json.loads(self.rfile.read(n) or b"{}")
                if not isinstance(data, dict):
                    raise ValueError
            except (ValueError, json.JSONDecodeError):
                return self.send_bytes(400, "application/json", b"{}")
            try:
                status, mime, body = PLUGIN_POST_ROUTES[self.path](data)
                return self.send_bytes(status, mime, body)
            except Exception as e:
                log("plugin POST", self.path, repr(e))
                return self.send_bytes(500, "application/json", b'{"ok":false}')
        if not self.host_ok() or self.path != "/bridge" or (origin and origin != PAGE_ORIGIN):
            return self.send_bytes(403, "text/plain", b"forbidden")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 8192:
                raise ValueError
            msg = json.loads(self.rfile.read(n) or b"{}")
            calls = BRIDGE.dispatch(str(msg.get("action", "")), str(msg.get("module", "")))
            return self.send_bytes(200, "application/json", json.dumps(calls, ensure_ascii=False).encode())
        except (ValueError, json.JSONDecodeError):
            return self.send_bytes(400, "application/json", b"[]")


def main():
    if not (ASSETS / "index.html").is_file():
        sys.exit(f"assets nao encontrados em {ASSETS}")
    MAPAS.mkdir(parents=True, exist_ok=True)
    harumi_system.use_car_output()
    log("plugins:", ", ".join(load_plugins()) or "nenhum")
    harumi_system.SpotifyWatcher(HUB.emit).start()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    srv.daemon_threads = True
    log(f"Harumi {VERSION} em http://{HOST}:{PORT}/assets/index.html  (dados: {MAPAS})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
