"""Fonte de GPS da Harumi: gpsd (127.0.0.1:2947) com simulador opcional. So biblioteca padrao.

- Thread unica: tenta o gpsd; sem gpsd, tenta de novo a cada 30 s e registra no log so a mudanca de estado.
- Simulador: desligado por padrao; liga com o store `gps.sim` = true (acao `gps.sim` com modulo on|off|toggle).
  So publica quando NAO ha fix real do gpsd nos ultimos 5 s.
- GET /linux/gps -> {ok, fonte: "gpsd"|"simulacao"|null, idade, fix, sim, gpsd}.
- Cada fix vai para a pagina pelo EventHub do servidor (SSE) como chamada `harumiGpsFix(fix)`.
  O plugin nao recebe o hub no carregamento (so as acoes recebem `emit`); por isso procuramos HUB.emit no modulo
  principal do servidor (sys.modules['__main__'] ou 'harumi_server') e, se nao achar, a primeira acao `gps.sim`
  entrega o `emit`. Sem nenhum, o modules/gps.js busca por GET /linux/gps (polling) - funciona igual, so mais lento."""
from __future__ import annotations

import json
import math
import socket
import sys
import threading
import time

import harumi_store

GPSD = ("127.0.0.1", 2947)
RETRY_S = 30
SIM_KEY = "gps.sim"
STALE_S = 10

_lock = threading.Lock()
_last: dict | None = None      # ultimo fix publicado
_seq = 0
_emit = None                    # fallback: emit entregue por uma acao
_gpsd_connected = False
_gpsd_fix_at = 0.0


def log(*a):
    try:
        print("[gps]", *a, file=sys.stderr, flush=True)
    except Exception:
        pass


def _hub_emit():
    for name in ("__main__", "harumi_server"):
        hub = getattr(sys.modules.get(name), "HUB", None)
        fn = getattr(hub, "emit", None)
        if callable(fn):
            return fn
    return _emit


def _publish(fix: dict) -> None:
    global _last, _seq
    with _lock:
        _seq += 1
        fix["seq"] = _seq
        fix["t"] = time.time()
        _last = fix
    emit = _hub_emit()
    if emit:
        try:
            emit("harumiGpsFix", fix)
        except Exception as e:
            log("emit falhou:", repr(e))


def _fnum(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


# ---------------------------------------------------------------- gpsd
def _gpsd_session() -> None:
    """Uma conexao ao gpsd; volta quando cair. Levanta OSError se nao conectar."""
    global _gpsd_connected, _gpsd_fix_at
    with socket.create_connection(GPSD, timeout=5) as s:
        s.settimeout(5)
        s.sendall(b'?WATCH={"enable":true,"json":true}\n')
        _gpsd_connected = True
        buf = b""
        while True:
            try:
                chunk = s.recv(4096)
            except socket.timeout:
                continue
            if not chunk:
                return
            buf += chunk
            if len(buf) > 65536:
                buf = b""
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(o, dict) or o.get("class") != "TPV":
                    continue
                lat, lon, mode = _fnum(o.get("lat")), _fnum(o.get("lon")), o.get("mode")
                if lat is None or lon is None or not isinstance(mode, int) or mode < 2:
                    continue  # sem fix 2D/3D
                sp = _fnum(o.get("speed"))
                tr = _fnum(o.get("track"))
                _gpsd_fix_at = time.time()
                _publish({"fonte": "gpsd", "lat": lat, "lon": lon, "speedMps": sp if sp is not None else 0.0,
                          "heading": tr, "mode": mode})


# ---------------------------------------------------------------- simulador
# Trajeto fechado no centro de Londrina/PR. Coordenadas aproximadas, escritas de memoria: [VERIFICAR]
# (conferir no mapa se os pontos caem em vias; o simulador apenas liga os pontos em linha reta).
SIM_ROUTE = [
    (-23.3105, -51.1630),  # [VERIFICAR] proximo da Praca Willie Davids
    (-23.3105, -51.1680),  # [VERIFICAR]
    (-23.3070, -51.1680),  # [VERIFICAR]
    (-23.3040, -51.1680),  # [VERIFICAR]
    (-23.3040, -51.1630),  # [VERIFICAR]
    (-23.3070, -51.1630),  # [VERIFICAR]
]
SIM_KMH = 40.0


def _dist_m(a, b) -> float:
    dy = (b[0] - a[0]) * 111320.0
    dx = (b[1] - a[1]) * 111320.0 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def _bearing(a, b) -> float:
    dy = b[0] - a[0]
    dx = (b[1] - a[1]) * math.cos(math.radians((a[0] + b[0]) / 2))
    return (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0


class _Sim:
    def __init__(self):
        self.i = 0          # segmento atual
        self.done_m = 0.0   # metros percorridos no segmento
        self.n = 0

    def step(self, dt: float) -> dict:
        pts = SIM_ROUTE
        a, b = pts[self.i], pts[(self.i + 1) % len(pts)]
        seg = _dist_m(a, b)
        # velocidade plausivel: 40 km/h com oscilacao lenta de +-6 km/h
        kmh = SIM_KMH + 6.0 * math.sin(self.n / 9.0)
        v = kmh / 3.6
        self.done_m += v * dt
        self.n += 1
        while self.done_m >= seg:
            self.done_m -= seg
            self.i = (self.i + 1) % len(pts)
            a, b = pts[self.i], pts[(self.i + 1) % len(pts)]
            seg = _dist_m(a, b)
        f = self.done_m / seg if seg else 0.0
        return {"fonte": "simulacao", "lat": a[0] + (b[0] - a[0]) * f, "lon": a[1] + (b[1] - a[1]) * f,
                "speedMps": v, "heading": _bearing(a, b), "mode": 3}


def sim_on() -> bool:
    return harumi_store.get(SIM_KEY, False) is True


# ---------------------------------------------------------------- thread
def _gpsd_loop() -> None:
    global _gpsd_connected
    quiet = False  # ja avisou que o gpsd esta fora; so volta a avisar depois de ter conectado
    while True:
        try:
            _gpsd_session()
        except OSError:
            pass
        except Exception as e:  # nunca derruba a thread
            log("gpsd erro:", repr(e))
        if _gpsd_connected:
            quiet = False
        _gpsd_connected = False
        if not quiet:
            log(f"gpsd indisponivel em {GPSD[0]}:{GPSD[1]}; nova tentativa a cada {RETRY_S} s")
            quiet = True
        time.sleep(RETRY_S)


def _sim_loop() -> None:
    sim = _Sim()
    while True:
        time.sleep(1.0)
        try:
            if sim_on() and time.time() - _gpsd_fix_at > 5.0:
                _publish(sim.step(1.0))
        except Exception as e:
            log("simulador erro:", repr(e))


def _start() -> None:
    for fn in (_gpsd_loop, _sim_loop):
        threading.Thread(target=fn, name="harumi-" + fn.__name__, daemon=True).start()


# ---------------------------------------------------------------- rotas
def _route(query):
    with _lock:
        fix = dict(_last) if _last else None
    age = round(time.time() - fix["t"], 1) if fix else None
    fresh = fix is not None and age is not None and age <= STALE_S
    body = {"ok": True, "fonte": fix["fonte"] if fresh else None, "idade": age,
            "fix": fix, "sim": sim_on(), "gpsd": _gpsd_connected}
    return 200, "application/json", json.dumps(body, ensure_ascii=False).encode()


def _action(module, emit):
    global _emit
    _emit = emit
    cur = sim_on()
    m = (module or "").strip().lower()
    new = (not cur) if m in ("", "toggle") else m in ("on", "1", "true")
    harumi_store.set(SIM_KEY, bool(new))
    return [{"fn": "__notify", "args": ["Simulador de GPS " + ("ligado" if new else "desligado")]}]


ROUTES = {"/linux/gps": _route}
ACTIONS = {"gps.sim": _action}

_start()
