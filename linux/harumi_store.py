"""Armazenamento JSON por chave da Harumi: ~/.local/share/harumi/store/<chave>.json.
Gravacao atomica (tmp no mesmo diretorio + fsync + os.replace), permissao 0600. So biblioteca padrao.
Diretorio base: variavel HARUMI_DATA (a mesma do servidor) ou ~/.local/share/harumi; pode ser trocado em
tempo de execucao com harumi_store.configure(caminho)."""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from pathlib import Path

KEY = re.compile(r"[a-z0-9_.-]{1,64}")
_lock = threading.Lock()
_dir: Path | None = None


def configure(path) -> None:
    global _dir
    _dir = Path(path)


def _base() -> Path:
    if _dir is not None:
        return _dir
    return Path(os.environ.get("HARUMI_DATA", Path.home() / ".local/share/harumi")) / "store"


def _file(key: str) -> Path:
    # "." sozinho ou ".." casariam na regex: o sufixo .json e a barra proibida impedem sair da pasta
    if not isinstance(key, str) or not KEY.fullmatch(key) or key.startswith("."):
        raise ValueError(f"chave invalida: {key!r}")
    return _base() / f"{key}.json"


def get(key: str, default=None):
    try:
        return json.loads(_file(key).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def set(key: str, value) -> None:  # noqa: A001 - nome pedido na especificacao
    f = _file(key)
    data = json.dumps(value, ensure_ascii=False).encode("utf-8")  # falha antes de tocar no disco
    with _lock:
        f.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=f.parent, prefix=".tmp-", suffix=".part")
        try:
            try:
                os.fchmod(fd, 0o600)
            except (AttributeError, OSError):
                pass  # Windows
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, f)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


def delete(key: str) -> bool:
    f = _file(key)
    with _lock:
        try:
            f.unlink()
            return True
        except FileNotFoundError:
            return False
