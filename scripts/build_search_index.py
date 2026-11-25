"""Gera o indice de busca offline (SQLite + FTS4) a partir do brasil.mbtiles (OpenMapTiles/planetiler).

Uso:
    python scripts/build_search_index.py [--mbtiles D:\\HarumiMapa\\saida\\brasil.mbtiles]
        [--out D:\\HarumiMapa\\saida\\busca-brasil.sqlite] [--workers 15] [--limit-chunks N]

Le so os tiles de zoom 14 (camadas place, poi, transportation_name, aerodrome_label, water_name) com um
decodificador protobuf minimo (sem dependencia externa; muito mais rapido que decodificar o tile inteiro).
Cidade/UF de cada item = municipio mais proximo de app/src/main/assets/cities-data.js (5534 municipios).
Esquema de saida:
    places(id, name, kind, city, uf, lat, lon, rank, norm)      -- dados para exibir
    busca  FTS4 contentless (docid = places.id; colunas name, kind, city, uf, todas normalizadas sem acento)
    meta(key, value)
O arquivo NAO contem segredos nem dados pessoais: so nomes publicos do OpenStreetMap (ODbL).
"""
import argparse, gzip, json, math, multiprocessing as mp, os, re, sqlite3, sys, time, unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CITIES_JS = ROOT / "app/src/main/assets/cities-data.js"
ZOOM = 14
EXTENT = 4096
CHUNK_COLS = 64          # colunas de tiles por tarefa
WANTED = {b"place", b"poi", b"transportation_name", b"aerodrome_label", b"water_name"}

UF_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará",
    "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}

# classe do OpenMapTiles -> tipo em pt-BR (None = descartar)
POI_KIND = {
    "fuel": "posto", "restaurant": "restaurante", "fast_food": "lanchonete", "cafe": "cafeteria",
    "bar": "bar", "pub": "bar", "ice_cream": "sorveteria", "lodging": "hotel", "hospital": "hospital",
    "doctors": "consultório", "pharmacy": "farmácia", "dentist": "dentista", "school": "escola",
    "kindergarten": "creche", "college": "universidade", "library": "biblioteca", "bank": "banco",
    "atm": None, "park": "parque", "stadium": "estádio", "place_of_worship": "igreja",
    "grocery": "mercado", "shop": "loja", "clothing_store": "loja", "bus": None, "railway": "estação",
    "aerialway": None, "town_hall": "prefeitura", "police": "delegacia", "post": "correios",
    "museum": "museu", "theatre": "teatro", "cinema": "cinema", "monument": "monumento",
    "attraction": "atração", "zoo": "zoológico", "campsite": "camping", "golf": "golfe",
    "swimming": "piscina", "playground": None, "parking": None, "fire_station": "bombeiros",
    "veterinary": "veterinário", "entrance": None, "harbor": "porto", "ferry_terminal": "balsa",
    "car": "oficina", "car_repair": "oficina", "laundry": "lavanderia", "hairdresser": None,
    "beauty": None, "office": "escritório", "florist": "loja", "jewelry": "loja", "art_gallery": "galeria",
    "music": "loja", "gym": "academia", "fitness_centre": "academia", "sports_centre": "ginásio",
    "pitch": "quadra", "cemetery": "cemitério", "marina": "marina", "picnic_site": "área de lazer",
    "viewpoint": "mirante", "information": None, "toilets": None, "drinking_water": None,
    "waste_basket": None, "bench": None, "recycling": None, "taxi": None, "bicycle_parking": None,
    "charging_station": "recarga",
}
POI_SUB_KIND = {
    "supermarket": "supermercado", "convenience": "conveniência", "marketplace": "feira",
    "department_store": "loja de departamentos", "mall": "shopping", "bakery": "padaria",
    "clinic": "clínica", "university": "universidade", "college": "faculdade",
    "bus_station": "rodoviária", "station": "estação", "hostel": "hostel", "motel": "motel",
    "guest_house": "pousada", "camp_site": "camping", "taxi": None, "bus_stop": None, "atm": None,
    "community_centre": "centro comunitário", "government": "órgão público", "car_repair": "oficina",
    "butcher": "açougue", "fishing": "pesqueiro", "chapel": "capela", "church": "igreja",
    "attraction": "atração", "artwork": None, "picnic_site": "área de lazer", "bus_stop ": None,
}
IMPORTANT_KINDS = {"hospital", "aeroporto", "rodoviária", "universidade", "faculdade", "shopping", "parque",
                   "estádio", "museu", "estação", "prefeitura", "teatro", "porto", "balsa", "atração",
                   "monumento", "mirante", "igreja"}
STREET_PREFIX = re.compile(r"^(rua|avenida|av\.|travessa|alameda|rodovia|estrada|pra[cç]a|largo|beco|via|marginal|viaduto|ponte|passarela|acesso)\b", re.I)


def norm(s):
    """Minusculas, sem acento, so [a-z0-9] separados por espaco. Igual a OfflineSearch.normalize no Android."""
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ---------------------------------------------------------------- protobuf minimo

def _varint(b, i):
    r = 0
    s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        if c < 0x80:
            return r, i
        s += 7


def _fields(b):
    """Itera (campo, wire, valor) de uma mensagem; valor = int (wire 0), bytes (wire 2) ou None."""
    i = 0
    n = len(b)
    while i < n:
        t, i = _varint(b, i)
        f, w = t >> 3, t & 7
        if w == 0:
            v, i = _varint(b, i)
            yield f, 0, v
        elif w == 2:
            ln, i = _varint(b, i)
            yield f, 2, b[i:i + ln]
            i += ln
        elif w == 5:
            i += 4
            yield f, 5, None
        elif w == 1:
            i += 8
            yield f, 1, None
        else:
            raise ValueError("wire type %d" % w)


def _packed(b):
    out = []
    i = 0
    n = len(b)
    while i < n:
        v, i = _varint(b, i)
        out.append(v)
    return out


def _value(b):
    for f, w, v in _fields(b):
        if f == 1:
            return v.decode("utf-8", "replace")
        if f in (4, 5):
            return v
        if f == 6:
            return (v >> 1) ^ -(v & 1)
        if f == 7:
            return bool(v)
    return None


def _first_points(geom, gtype):
    """Vertices (px,py) da primeira geometria: ponto -> [p]; linha -> vertices da primeira linestring."""
    pts = []
    x = y = 0
    i = 0
    n = len(geom)
    cmds = _packed(geom)
    k = 0
    started = False
    while k < len(cmds):
        c = cmds[k]
        k += 1
        cid, cnt = c & 7, c >> 3
        if cid == 7:
            continue
        for _ in range(cnt):
            dx = cmds[k]
            dy = cmds[k + 1]
            k += 2
            x += (dx >> 1) ^ -(dx & 1)
            y += (dy >> 1) ^ -(dy & 1)
            if cid == 1 and started and gtype == 2:
                return pts          # segunda linestring: para
            pts.append((x, y))
            if gtype == 1:
                return pts
        started = True
    return pts


def parse_tile(raw):
    """Devolve {camada: [(props, pontos)]} so das camadas WANTED."""
    out = {}
    for f, w, lb in _fields(raw):
        if f != 3:
            continue
        name = None
        for lf, lw, lv in _fields(lb):
            if lf == 1:
                name = lv
                break
        if name not in WANTED:
            continue
        keys, vals, feats = [], [], []
        for lf, lw, lv in _fields(lb):
            if lf == 3:
                keys.append(lv.decode("utf-8", "replace"))
            elif lf == 4:
                vals.append(_value(lv))
            elif lf == 2:
                feats.append(lv)
        res = []
        for fb in feats:
            tags = geom = None
            gtype = 0
            for ff, fw, fv in _fields(fb):
                if ff == 2:
                    tags = fv
                elif ff == 3:
                    gtype = fv
                elif ff == 4:
                    geom = fv
            if tags is None or geom is None:
                continue
            t = _packed(tags)
            props = {}
            for j in range(0, len(t) - 1, 2):
                kname = keys[t[j]]
                if kname in ("name", "class", "subclass", "rank", "ref", "network", "iata"):
                    props[kname] = vals[t[j + 1]]
            if "name" not in props and "ref" not in props:
                continue
            res.append((props, _first_points(geom, gtype), gtype))
        out[name.decode()] = res
    return out


# ---------------------------------------------------------------- geometria / cidades

def _tile_lonlat(tx, ty, px, py):
    n = 1 << ZOOM
    lon = (tx + px / EXTENT) / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty + py / EXTENT) / n))))
    return lat, lon


def load_cities():
    s = CITIES_JS.read_text(encoding="utf-8")
    data = json.loads(s[s.index("["):s.rindex("]") + 1])
    return data


_G = {}


def _init_worker(mbtiles, cities):
    _G["db"] = sqlite3.connect("file:%s?mode=ro" % Path(mbtiles).as_posix(), uri=True)
    _G["lat"] = np.array([c["lat"] for c in cities])
    _G["lon"] = np.array([c["lon"] for c in cities])


def _street_ok(name, cls, sub):
    if cls == "service":
        return bool(name and STREET_PREFIX.match(name))
    if cls in ("track", "raceway", "bridleway", "cycleway"):
        return False
    if cls == "path":
        return sub == "pedestrian" and bool(name)
    return True


def process_chunk(args):
    c0, c1 = args
    db = _G["db"]
    clat, clon = _G["lat"], _G["lon"]
    pois, streets, places = [], [], []
    ntiles = 0
    cur = db.execute("select tile_column, tile_row, tile_data from tiles where zoom_level=? and tile_column>=? and tile_column<? ",
                     (ZOOM, c0, c1))
    for tx, row, data in cur:
        ntiles += 1
        ty = (1 << ZOOM) - 1 - row
        try:
            layers = parse_tile(gzip.decompress(data))
        except Exception:
            continue
        items = []     # (tipo, props, lat, lon)
        seen_street = set()
        for lname, feats in layers.items():
            for props, pts, gtype in feats:
                if not pts:
                    continue
                if lname == "transportation_name":
                    inside = [p for p in pts if 0 <= p[0] < EXTENT and 0 <= p[1] < EXTENT]
                    if not inside:
                        continue
                    p = inside[len(inside) // 2]
                    nm = props.get("name")
                    ref = props.get("ref")
                    if nm is None and ref is None:
                        continue
                    k = (nm, ref)
                    if k in seen_street:
                        continue
                    seen_street.add(k)
                    if not _street_ok(nm, props.get("class"), props.get("subclass")):
                        continue
                else:
                    p = pts[0]
                    if not (0 <= p[0] < EXTENT and 0 <= p[1] < EXTENT):
                        continue
                    if not props.get("name"):
                        continue
                lat, lon = _tile_lonlat(tx, ty, p[0], p[1])
                items.append((lname, props, lat, lon))
        if not items:
            continue
        # cidades candidatas = proximas do centro do tile (margem de ~0,1 grau)
        mlat, mlon = _tile_lonlat(tx, ty, EXTENT / 2, EXTENT / 2)
        kx = math.cos(math.radians(mlat))
        d0 = (clat - mlat) ** 2 + ((clon - mlon) * kx) ** 2
        near = math.sqrt(d0.min())
        cand = np.nonzero(d0 <= (near + 0.12) ** 2)[0]
        ilat = np.array([it[2] for it in items])
        ilon = np.array([it[3] for it in items])
        dd = (clat[cand][None, :] - ilat[:, None]) ** 2 + ((clon[cand][None, :] - ilon[:, None]) * kx) ** 2
        best = cand[dd.argmin(axis=1)]
        for it, ci in zip(items, best):
            lname, props, lat, lon = it
            ci = int(ci)
            if lname == "poi":
                pois.append((props.get("name"), props.get("class"), props.get("subclass"), props.get("rank"), ci, lat, lon))
            elif lname == "place":
                places.append((props.get("name"), props.get("class"), props.get("rank"), ci, lat, lon))
            elif lname == "aerodrome_label":
                pois.append((props.get("name"), "aerodrome", props.get("class"), None, ci, lat, lon))
            elif lname == "water_name":
                pois.append((props.get("name"), "water", props.get("class"), None, ci, lat, lon))
            else:
                streets.append((props.get("name"), props.get("ref"), props.get("class"), props.get("network"), ci, lat, lon))
    # agrega ruas por (nome, ref, cidade) dentro do chunk: soma + ponto mais proximo da media
    agg = {}
    for nm, ref, cls, net, ci, lat, lon in streets:
        k = (nm, ref, ci)
        a = agg.get(k)
        if a is None:
            agg[k] = [cls, net, 1, lat, lon, [(lat, lon)]]
        else:
            a[2] += 1
            a[3] += lat
            a[4] += lon
            if len(a[5]) < 40:
                a[5].append((lat, lon))
    srows = []
    for (nm, ref, ci), (cls, net, n, sl, so, samp) in agg.items():
        ml, mo = sl / n, so / n
        bl, bo = min(samp, key=lambda q: (q[0] - ml) ** 2 + (q[1] - mo) ** 2)
        srows.append((nm, ref, ci, cls, net, n, bl, bo))
    return ntiles, pois, srows, places


# ---------------------------------------------------------------- montagem

def poi_kind(cls, sub):
    if cls == "aerodrome":
        return "aeroporto" if sub not in ("heliport", "helipad") else "heliponto"
    if cls == "water":
        return "água"
    if sub in POI_SUB_KIND:
        return POI_SUB_KIND[sub]
    if cls in POI_KIND:
        return POI_KIND[cls]
    return "local"


def street_kind(nm, ref):
    if nm is None:
        return "rodovia"
    n = norm(nm)
    if n.startswith(("rodovia", "br ", "estrada")) or (ref and re.match(r"^[A-Z]{2,3}-\d", ref) and n.startswith(("rodovia", "br"))):
        return "rodovia"
    if n.startswith(("praca", "largo")):
        return "praça"
    return "rua"


def dist_km(la1, lo1, la2, lo2):
    return math.hypot((la1 - la2) * 111.0, (lo1 - lo2) * 111.0 * math.cos(math.radians(la1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mbtiles", default=r"D:\HarumiMapa\saida\brasil.mbtiles")
    ap.add_argument("--out", default=r"D:\HarumiMapa\saida\busca-brasil.sqlite")
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--limit-chunks", type=int, default=0, help="so para teste")
    ap.add_argument("--stage", default=r"D:\HarumiMapa\tmp-busca\staging.sqlite")
    a = ap.parse_args()
    t0 = time.time()
    cities = load_cities()
    ncity = len(cities)
    Path(a.stage).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(a.stage):
        os.remove(a.stage)
    st = sqlite3.connect(a.stage)
    st.executescript("""PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
        CREATE TABLE poi(name, cls, sub, rank, ci, lat, lon);
        CREATE TABLE street(name, ref, ci, cls, net, n, lat, lon);
        CREATE TABLE place(name, cls, rank, ci, lat, lon);""")
    ro = sqlite3.connect("file:%s?mode=ro" % Path(a.mbtiles).as_posix(), uri=True)
    cmin, cmax = ro.execute("select min(tile_column), max(tile_column) from tiles where zoom_level=?", (ZOOM,)).fetchone()
    ro.close()
    chunks = [(c, min(c + CHUNK_COLS, cmax + 1)) for c in range(cmin, cmax + 1, CHUNK_COLS)]
    if a.limit_chunks:
        mid = len(chunks) // 2
        chunks = chunks[mid:mid + a.limit_chunks]
    print("chunks:", len(chunks), "colunas", cmin, "-", cmax, flush=True)
    done = tiles = 0
    with mp.Pool(a.workers, initializer=_init_worker, initargs=(a.mbtiles, cities)) as pool:
        for nt, pois, srows, places in pool.imap_unordered(process_chunk, chunks):
            st.executemany("insert into poi values (?,?,?,?,?,?,?)", pois)
            st.executemany("insert into street values (?,?,?,?,?,?,?,?)", srows)
            st.executemany("insert into place values (?,?,?,?,?,?)", places)
            done += 1
            tiles += nt
            if done % 10 == 0 or done == len(chunks):
                print("  %d/%d chunks, %d tiles, %.0fs" % (done, len(chunks), tiles, time.time() - t0), flush=True)
    st.commit()
    t_read = time.time() - t0
    print("leitura: %.0fs, %d tiles" % (t_read, tiles), flush=True)

    # ---- monta linhas candidatas (cand) com rank, em streaming
    pop = [max(0, c.get("population") or 0) for c in cities]
    cbonus = [min(8.0, math.log10(p + 1) * 1.2) for p in pop]
    st.executescript("CREATE TABLE cand(name, kind, ci, uf, lat, lon, rank, norm, ext);")
    ins = "insert into cand values (?,?,?,?,?,?,?,?,?)"
    buf = []

    def push(name, kind, ci, uf, lat, lon, rank, ext=""):
        nn = norm(name)
        if len(nn) < 2:
            return
        buf.append((name, kind, ci, uf, lat, lon, rank, nn, ext))
        if len(buf) >= 50000:
            st.executemany(ins, buf)
            buf.clear()

    # estados e municipios (cities-data.js)
    byuf = {}
    for i, c in enumerate(cities):
        byuf.setdefault(c["uf"], []).append(i)
        push(c["name"], "cidade", i, c["uf"], c["lat"], c["lon"], 70 + min(25.0, math.log10(pop[i] + 1) * 4))
    for uf, idxs in byuf.items():
        la = sum(cities[i]["lat"] for i in idxs) / len(idxs)
        lo = sum(cities[i]["lon"] for i in idxs) / len(idxs)
        # cidade mais populosa do estado como ancora (centroide pode cair fora do territorio)
        top = max(idxs, key=lambda i: pop[i])
        push(UF_NAMES[uf], "estado", top, uf, cities[top]["lat"], cities[top]["lon"], 100)
    cnorm = {}
    for i, c in enumerate(cities):
        cnorm.setdefault(norm(c["name"]), []).append(i)

    # lugares OSM
    PL = {"suburb": ("bairro", 55), "neighbourhood": ("bairro", 50), "quarter": ("bairro", 50),
          "village": ("povoado", 45), "hamlet": ("povoado", 40), "island": ("ilha", 45),
          "city": ("cidade", 68), "town": ("cidade", 66)}
    for nm, cls, rk, ci, lat, lon in st.execute("select name, cls, rank, ci, lat, lon from place"):
        if cls not in PL:
            continue
        kind, base = PL[cls]
        if cls in ("city", "town"):
            if any(dist_km(lat, lon, cities[j]["lat"], cities[j]["lon"]) < 25 for j in cnorm.get(norm(nm), [])):
                continue          # ja existe como municipio
            kind = "distrito"
        push(nm, kind, ci, cities[ci]["uf"], lat, lon, base + cbonus[ci] * 0.5)
    # POIs
    skipped = 0
    for nm, cls, sub, rk, ci, lat, lon in st.execute("select name, cls, sub, rank, ci, lat, lon from poi"):
        kind = poi_kind(cls, sub)
        if kind is None:
            skipped += 1
            continue
        base = 55 if kind in IMPORTANT_KINDS else (35 if kind != "local" else 28)
        if kind == "aeroporto":
            base = 75
        push(nm, kind, ci, cities[ci]["uf"], lat, lon, base + cbonus[ci])
    # ruas: junta os chunks por (nome, ref, cidade)
    cur = st.execute("select name, ref, ci, cls, net, n, lat, lon from street order by name, ref, ci")
    group, gk = [], None

    def flush(group):
        nm, ref, ci = gk
        tot = sum(g[5] for g in group)
        ml = sum(g[6] * g[5] for g in group) / tot
        mo = sum(g[7] * g[5] for g in group) / tot
        bl, bo = min(((g[6], g[7]) for g in group), key=lambda q: (q[0] - ml) ** 2 + (q[1] - mo) ** 2)
        kind = street_kind(nm, ref)
        if nm is None:
            disp, ext = ref, ""
        else:
            disp, ext = nm, (ref or "")
        if kind == "rodovia" and nm is not None and ref and norm(ref) not in norm(nm):
            disp = "%s (%s)" % (nm, ref)
        rank = (45 if kind == "rodovia" else 25) + cbonus[ci]
        push(disp, kind, ci, cities[ci]["uf"], bl, bo, rank, ext)

    for row in cur:
        k = (row[0], row[1], row[2])
        if k != gk and group:
            flush(group)
            group = []
        gk = k
        group.append(row)
    if group:
        flush(group)
    if buf:
        st.executemany(ins, buf)
        buf.clear()
    st.commit()
    ncand = st.execute("select count(*) from cand").fetchone()[0]
    print("candidatos: %d (pois descartados por classe: %d), %.0fs" % (ncand, skipped, time.time() - t0), flush=True)

    # ---- saida final: ordenada por rank desc (docid baixo = mais relevante -> LIMIT no FTS pega os melhores)
    if os.path.exists(a.out):
        os.remove(a.out)
    out = sqlite3.connect(a.out)
    out.executescript("""PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA page_size=4096;
        CREATE TABLE places(id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, city TEXT, uf TEXT,
            lat REAL NOT NULL, lon REAL NOT NULL, rank INTEGER NOT NULL, norm TEXT NOT NULL);
        CREATE VIRTUAL TABLE busca USING fts4(content="", name, kind, city, uf, tokenize=simple);
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);""")
    # dedupe: mesmo (norm, kind, cidade) a menos de 150 m -> mantem o primeiro (maior rank)
    last = {}
    kept = 0
    pb, fb = [], []
    cur = st.execute("select name, kind, ci, uf, lat, lon, rank, norm, ext from cand order by rank desc, norm")
    for nm, kind, ci, uf, lat, lon, rank, nn, ext in cur:
        key = (nn, kind, ci)
        if kind not in ("cidade", "estado"):
            prev = last.get(key)
            if prev is not None and any(abs(p[0] - lat) < 0.0014 and abs(p[1] - lon) < 0.0016 for p in prev):
                continue
            last.setdefault(key, []).append((lat, lon))
        kept += 1
        city = cities[ci]["name"] if kind != "estado" else ""
        pb.append((kept, nm, kind, city, uf, round(lat, 5), round(lon, 5), int(round(rank)), nn))
        sname = (nn + " " + norm(ext)) if ext else nn
        fb.append((kept, sname, "" if kind in ("rua", "rodovia", "cidade", "estado") else norm(kind), norm(city), uf.lower()))
        if len(pb) >= 50000:
            out.executemany("insert into places values (?,?,?,?,?,?,?,?,?)", pb)
            out.executemany("insert into busca(docid, name, kind, city, uf) values (?,?,?,?,?)", fb)
            pb.clear()
            fb.clear()
            if len(last) > 3_000_000:
                last.clear()
    if pb:
        out.executemany("insert into places values (?,?,?,?,?,?,?,?,?)", pb)
        out.executemany("insert into busca(docid, name, kind, city, uf) values (?,?,?,?,?)", fb)
    out.execute("insert into busca(busca) values ('optimize')")
    out.execute("CREATE INDEX places_kind_norm ON places(kind, norm)")
    out.execute("CREATE INDEX places_kind_geo ON places(kind, lat, lon)")
    out.executemany("insert into meta values (?,?)", [
        ("fonte", "OpenStreetMap contributors (ODbL) via OpenMapTiles/planetiler, brasil.mbtiles z14"),
        ("gerado_em", time.strftime("%Y-%m-%d %H:%M:%S")), ("linhas", str(kept)), ("fts", "FTS4 contentless: name, kind, city, uf")])
    out.commit()
    out.execute("VACUUM")
    out.close()
    st.close()
    try:
        os.remove(a.stage)
    except OSError:
        pass
    size = os.path.getsize(a.out)
    print("PRONTO: %d linhas, %.1f MB, tempo total %.0fs (leitura %.0fs)" % (kept, size / 1e6, time.time() - t0, t_read), flush=True)


if __name__ == "__main__":
    mp.freeze_support()
    main()
