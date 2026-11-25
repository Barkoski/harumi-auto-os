"""Estado do sistema para a Harumi OS: temperatura, volume (PipeWire/wpctl) e musica tocando no Spotify (librespot).

O librespot chama spotify_event.py a cada evento (--onevent); esse script grava ~/.cache/harumi/spotify-now.json,
que o servidor le e repassa a interface.
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

NOW_FILE = Path.home() / ".cache/harumi/spotify-now.json"
ENV = dict(os.environ, XDG_RUNTIME_DIR=os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))


def temperature_c():
    vals = []
    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            vals.append(int(open(f).read()) / 1000)
        except (OSError, ValueError):
            pass
    return round(max(vals)) if vals else None


def _wpctl(*args, timeout=3):
    return subprocess.run(["wpctl", *args], capture_output=True, text=True, timeout=timeout, env=ENV)


def volume():
    """{'percent': 0-100, 'muted': bool} do alto-falante padrao, ou None."""
    try:
        out = _wpctl("get-volume", "@DEFAULT_AUDIO_SINK@").stdout  # ex.: "Volume: 0.40 [MUTED]"
        m = re.search(r"Volume:\s*([0-9.]+)", out)
        if not m:
            return None
        return {"percent": round(float(m.group(1)) * 100), "muted": "MUTED" in out}
    except (OSError, subprocess.SubprocessError):
        return None


def set_volume(percent: int):
    percent = max(0, min(100, int(percent)))
    _wpctl("set-volume", "@DEFAULT_AUDIO_SINK@", f"{percent / 100:.2f}")
    return volume()


def step_volume(delta: int):
    v = volume() or {"percent": 40}
    return set_volume(v["percent"] + int(delta))


def toggle_mute():
    _wpctl("set-mute", "@DEFAULT_AUDIO_SINK@", "toggle")
    return volume()


def use_car_output():
    """Saida padrao = P2 da placa (ES8388), que vai para o som do carro. Ignora se nao achar."""
    try:
        out = _wpctl("status").stdout
        sinks = out.split("Sinks:", 1)[1].split("Sources:", 1)[0] if "Sinks:" in out else ""
        m = re.search(r"(\d+)\.\s+ES8388[^\n]*", sinks)
        if m:
            _wpctl("set-default", m.group(1))
    except (OSError, subprocess.SubprocessError, IndexError):
        pass


def spotify_now():
    try:
        d = json.loads(NOW_FILE.read_text())
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


_health = {"online": None, "llm": None}
MBTILES = Path.home() / ".local/share/harumi/mapas/brasil.mbtiles"


def _check_health():
    """A cada 20 s: Internet (TCP 443 em dois provedores) e IA local (/health do llama-server)."""
    import socket
    import urllib.request
    while True:
        online = False
        for host in ("tiles.openfreemap.org", "1.1.1.1"):
            try:
                with socket.create_connection((host, 443), timeout=2):
                    online = True
                    break
            except OSError:
                pass
        try:
            with urllib.request.urlopen("http://127.0.0.1:8090/health", timeout=1) as r:
                llm = r.status == 200
        except OSError:
            llm = False
        _health.update(online=online, llm=llm)
        time.sleep(20)


threading.Thread(target=_check_health, daemon=True).start()


def status():
    return {"tempC": temperature_c(), "volume": volume(), "spotify": spotify_now(), "time": int(time.time()),
            "online": _health["online"], "llm": _health["llm"], "mapOffline": MBTILES.is_file()}


class SpotifyWatcher(threading.Thread):
    """Avisa a interface (emit) quando a musica muda."""

    def __init__(self, emit):
        super().__init__(daemon=True)
        self.emit = emit

    def run(self):
        last = None
        while True:
            try:
                m = NOW_FILE.stat().st_mtime
            except OSError:
                m = None
            if m != last:
                last = m
                now = spotify_now()
                if now:
                    self.emit("harumiSpotifyNow", now)
            time.sleep(1)
