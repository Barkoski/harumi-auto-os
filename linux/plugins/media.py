"""Capa do album da musica tocando no Spotify (dispositivo Harumi).

A pagina so carrega imagens da propria Harumi (CSP img-src 'self'), entao o servidor busca a capa e a guarda em cache.
So aceita endereco https://i.scdn.co/ (servidor de imagens do Spotify) vindo do arquivo que o librespot grava.
GET /linux/spotify-cover -> image/jpeg da musica atual (404 sem capa).
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path

NOW = Path.home() / ".cache/harumi/spotify-now.json"
CACHE = Path.home() / ".cache/harumi/covers"
ALLOWED = re.compile(r"https://i\.scdn\.co/image/[A-Za-z0-9]{8,80}")
MAX_BYTES = 2_000_000
KEEP = 40


def _json(code, obj):
    return code, "application/json", json.dumps(obj).encode()


def current_cover_url():
    try:
        url = json.loads(NOW.read_text()).get("cover", "")
    except (OSError, ValueError, AttributeError):
        return None
    return url if isinstance(url, str) and ALLOWED.fullmatch(url) else None


def fetch(url) -> bytes | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:32] + ".jpg")
    if f.is_file():
        return f.read_bytes()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HarumiOS"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = r.read(MAX_BYTES + 1)
    except OSError:
        return None
    if len(data) > MAX_BYTES or not data.startswith(b"\xff\xd8"):  # so JPEG
        return None
    tmp = f.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(f)
    old = sorted(CACHE.glob("*.jpg"), key=lambda p: p.stat().st_mtime)[:-KEEP]
    for p in old:
        p.unlink(missing_ok=True)
    return data


def _cover(query):
    url = current_cover_url()
    data = fetch(url) if url else None
    if not data:
        return _json(404, {"ok": False})
    return 200, "image/jpeg", data


ROUTES = {"/linux/spotify-cover": _cover}
