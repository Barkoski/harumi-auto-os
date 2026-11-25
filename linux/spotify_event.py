#!/usr/bin/env python3
"""Chamado pelo librespot (--onevent) a cada evento do player. Grava o estado em ~/.cache/harumi/spotify-now.json.
Variaveis do librespot usadas (se existirem): PLAYER_EVENT, TRACK_ID, NAME, ARTISTS, ALBUM, COVERS, DURATION_MS, POSITION_MS."""
import json
import os
import time
from pathlib import Path

OUT = Path.home() / ".cache/harumi/spotify-now.json"
ev = os.environ.get("PLAYER_EVENT", "")
try:
    cur = json.loads(OUT.read_text())
except (OSError, ValueError):
    cur = {}

if ev in ("track_changed", "playing", "paused", "stopped", "started", "loading", "end_of_track", "preloading"):
    if os.environ.get("NAME"):
        covers = [c for c in os.environ.get("COVERS", "").split("\n") if c.startswith("https://")]
        cur.update({"name": os.environ.get("NAME", ""), "artists": os.environ.get("ARTISTS", "").replace("\n", ", "),
                    "album": os.environ.get("ALBUM", ""), "cover": covers[0] if covers else "",
                    "durationMs": int(os.environ.get("DURATION_MS") or 0), "trackId": os.environ.get("TRACK_ID", "")})
    if ev in ("playing", "paused", "stopped"):
        cur["state"] = ev
        cur["positionMs"] = int(os.environ.get("POSITION_MS") or 0)
    cur["event"] = ev
    cur["at"] = int(time.time())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(cur, ensure_ascii=False))
    os.replace(tmp, OUT)
