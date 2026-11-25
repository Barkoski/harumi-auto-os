"""Privacidade da Harumi: modo manobrista (PIN) e "Apagar meus dados".

Rotas (POST com checagem de Host+Origin feita pelo servidor):
  GET  /linux/privacy         -> {valet, pinSet, waitS}
  POST /linux/privacy-pin     {pin, current?}      define/troca o PIN (4 a 8 digitos); troca exige o PIN atual
  POST /linux/privacy-valet   {on, pin?}           liga (precisa de PIN definido) ou desliga (exige o PIN)
  POST /linux/privacy-wipe    {confirm:"APAGAR", pin?}  apaga store + spotify-now.json (PIN se o modo estiver ligado)

O PIN nunca e gravado nem registrado em claro: PBKDF2-HMAC-SHA256, sal de 16 bytes, 300 000 iteracoes, arquivo
~/.local/share/harumi/privacy.json (modo 0600, FORA da pasta store, entao o "apagar dados" nao leva o PIN junto).
Tentativas erradas: a partir da 5a, espera de 30 s que dobra a cada erro (maximo 1 h); persiste entre reinicios."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from pathlib import Path

import harumi_store

ITER = 300_000
MAX_FREE = 5          # erros sem espera
BASE_WAIT = 30        # s, depois do 5o erro
MAX_WAIT = 3600
PIN_RE = re.compile(r"[0-9]{4,8}")
_lock = threading.Lock()


def _file() -> Path:
    return Path(os.environ.get("HARUMI_DATA", Path.home() / ".local/share/harumi")) / "privacy.json"


def _load() -> dict:
    try:
        d = json.loads(_file().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(d: dict) -> None:
    f = _file()
    f.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=f.parent, prefix=".tmp-priv-", suffix=".part")
    try:
        try:
            os.fchmod(fd, 0o600)
        except (AttributeError, OSError):
            pass  # Windows
        with os.fdopen(fd, "wb") as fh:
            fh.write(json.dumps(d).encode("utf-8"))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, f)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _hash(pin: str, salt: bytes, iters: int = ITER) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iters)


def _wait_left(d: dict) -> int:
    return max(0, int(d.get("until", 0) - time.time() + 0.999))


def _check_pin(d: dict, pin) -> tuple[bool, int]:
    """(ok, espera_em_segundos). Conta a falha e persiste. Chamar com _lock."""
    w = _wait_left(d)
    if w:
        return False, w
    if not isinstance(pin, str) or not PIN_RE.fullmatch(pin) or not d.get("hash"):
        ok = False
        # gasta o mesmo tempo para nao distinguir "formato errado" de "PIN errado"
        _hash("0000", b"\0" * 16)
    else:
        try:
            salt = bytes.fromhex(d["salt"])
            want = bytes.fromhex(d["hash"])
            ok = hmac.compare_digest(_hash(pin, salt, int(d.get("iter", ITER))), want)
        except (ValueError, KeyError, TypeError):
            ok = False
    if ok:
        if d.get("fails") or d.get("until"):
            d["fails"] = 0
            d["until"] = 0
            _save(d)
        return True, 0
    d["fails"] = int(d.get("fails", 0)) + 1
    if d["fails"] >= MAX_FREE:
        wait = min(MAX_WAIT, BASE_WAIT * (2 ** (d["fails"] - MAX_FREE)))
        d["until"] = time.time() + wait
    _save(d)
    return False, _wait_left(d)


def _json(status: int, obj: dict):
    return status, "application/json", json.dumps(obj, ensure_ascii=False).encode()


def _denied(wait: int):
    if wait:
        return _json(429, {"ok": False, "error": "espera", "waitS": wait})
    return _json(403, {"ok": False, "error": "pin"})


def _state(d: dict) -> dict:
    return {"valet": bool(d.get("valet")), "pinSet": bool(d.get("hash")), "waitS": _wait_left(d)}


def _get(query):
    with _lock:
        return _json(200, {"ok": True, **_state(_load())})


def _post_pin(data):
    new = data.get("pin")
    if not isinstance(new, str) or not PIN_RE.fullmatch(new):
        return _json(400, {"ok": False, "error": "formato"})
    with _lock:
        d = _load()
        if d.get("hash"):
            ok, wait = _check_pin(d, data.get("current"))
            if not ok:
                return _denied(wait)
        salt = secrets.token_bytes(16)
        d.update(salt=salt.hex(), hash=_hash(new, salt).hex(), iter=ITER, fails=0, until=0)
        _save(d)
        return _json(200, {"ok": True, **_state(d)})


def _post_valet(data):
    on = data.get("on")
    if not isinstance(on, bool):
        return _json(400, {"ok": False, "error": "formato"})
    with _lock:
        d = _load()
        if on:
            if not d.get("hash"):
                return _json(409, {"ok": False, "error": "sem-pin"})
        else:
            if d.get("valet"):
                ok, wait = _check_pin(d, data.get("pin"))
                if not ok:
                    return _denied(wait)
        d["valet"] = on
        _save(d)
        return _json(200, {"ok": True, **_state(d)})


def _wipe_files() -> list:
    removed = []
    base = harumi_store._base()
    if base.is_dir():
        for c in list(base.iterdir()):
            try:
                if c.is_dir() and not c.is_symlink():
                    shutil.rmtree(c)
                else:
                    c.unlink()
                removed.append(c.name)
            except OSError:
                pass
    now = Path.home() / ".cache/harumi/spotify-now.json"
    try:
        now.unlink()
        removed.append(now.name)
    except OSError:
        pass
    return removed


def _post_wipe(data):
    if data.get("confirm") != "APAGAR":
        return _json(400, {"ok": False, "error": "confirmacao"})
    with _lock:
        d = _load()
        if d.get("valet"):
            ok, wait = _check_pin(d, data.get("pin"))
            if not ok:
                return _denied(wait)
        n = len(_wipe_files())
    return _json(200, {"ok": True, "removed": n})


ROUTES = {"/linux/privacy": _get}
POST_ROUTES = {"/linux/privacy-pin": _post_pin, "/linux/privacy-valet": _post_valet, "/linux/privacy-wipe": _post_wipe}
