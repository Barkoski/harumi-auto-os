"""Politica termica: pausa a IA local (harumi-llm) quando a placa esquenta e religa quando esfria.

Le a temperatura a cada 10 s (harumi_system.temperature_c, a maior zona termica). Acima de HI (padrao 80 C) por
2 leituras seguidas: `systemctl --user stop harumi-llm`. Abaixo de LO (padrao 70 C) por 3 leituras seguidas:
`systemctl --user start harumi-llm`, mas SO se foi esta politica que a parou (IA parada pelo usuario nao e religada).
Limites em harumi_store: "thermal.hi" e "thermal.lo" (invalidos ou hi <= lo -> padroes).
GET /linux/thermal -> {tempC, paused, hi, lo, service, error}."""
from __future__ import annotations

import json
import subprocess
import threading
import time

import harumi_store

try:
    import harumi_system
except Exception:  # pragma: no cover - fora da placa
    harumi_system = None

SERVICE = "harumi-llm.service"
INTERVAL = 10
HI_DEFAULT, LO_DEFAULT = 80, 70
HI_READS, LO_READS = 2, 3

_state = {"tempC": None, "paused": False, "hot": 0, "cool": 0, "error": None}
_lock = threading.Lock()
_started = False


def limits() -> tuple:
    hi, lo = harumi_store.get("thermal.hi", HI_DEFAULT), harumi_store.get("thermal.lo", LO_DEFAULT)
    ok = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (hi, lo))
    if not ok or not (50 <= lo < hi <= 100):
        return HI_DEFAULT, LO_DEFAULT
    return hi, lo


def read_temp():
    if harumi_system is not None:
        return harumi_system.temperature_c()
    return None


def _systemctl(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, timeout=20)


def _active() -> bool:
    try:
        return _systemctl("is-active", SERVICE).stdout.strip() == "active"
    except (OSError, subprocess.SubprocessError):
        return False


def step(temp) -> None:
    """Uma leitura da politica (separada do laco para poder ser testada)."""
    hi, lo = limits()
    with _lock:
        _state["tempC"] = temp
        if temp is None:
            _state["hot"] = _state["cool"] = 0
            return
        _state["hot"] = _state["hot"] + 1 if temp > hi else 0
        _state["cool"] = _state["cool"] + 1 if temp < lo else 0
        if not _state["paused"] and _state["hot"] >= HI_READS:
            if _active():  # so assume a pausa se a IA estava ligada; parada pelo usuario fica como esta
                r = _systemctl("stop", SERVICE)
                if r.returncode == 0:
                    _state["paused"] = True
                    _state["error"] = None
                else:
                    _state["error"] = "stop falhou"
            _state["hot"] = 0
        elif _state["paused"] and _state["cool"] >= LO_READS:
            if _active():  # alguem ja religou
                _state["paused"] = False
            else:
                r = _systemctl("start", SERVICE)
                if r.returncode == 0:
                    _state["paused"] = False
                    _state["error"] = None
                else:
                    _state["error"] = "start falhou"
            _state["cool"] = 0


def _loop() -> None:
    while True:
        try:
            step(read_temp())
        except Exception as e:  # o laco nunca morre
            with _lock:
                _state["error"] = type(e).__name__
        time.sleep(INTERVAL)


def _get(query):
    hi, lo = limits()
    with _lock:
        out = {"ok": True, "tempC": _state["tempC"], "paused": _state["paused"], "hi": hi, "lo": lo,
               "service": SERVICE, "error": _state["error"]}
    return 200, "application/json", json.dumps(out).encode()


def _start() -> None:
    global _started
    if not _started:
        _started = True
        threading.Thread(target=_loop, name="harumi-thermal", daemon=True).start()


_start()

ROUTES = {"/linux/thermal": _get}
