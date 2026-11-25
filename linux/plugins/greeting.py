"""Saudacao ao ligar: jingle japones original + "Irasshaimase! Seja bem-vindo!" + pergunta do destino.

Quando toca:
  - uma vez por partida da placa (boot_id do kernel): a Harumi liga junto com o carro (pos-chave);
  - quando outro plugin chamar trigger() — reservado para o interruptor da porta no GPIO (ainda nao instalado);
  - pelo botao "Tocar saudação" em Ajustes.
Jingle: composto aqui mesmo (escala pentatonica japonesa "yo", timbre de sino), gerado em WAV na primeira vez.
Voz em japones: so se houver um sintetizador instalado (Open JTalk); sem ele, a saudacao aparece escrita.
Rotas: GET /linux/greeting (deve tocar?), GET /linux/greeting-jingle (audio/wav), GET /linux/greeting-voice
(audio/wav, 404 sem sintetizador), POST /linux/greeting-done, POST /linux/greeting-test.
"""
from __future__ import annotations

import io
import json
import math
import os
import shutil
import struct
import subprocess
import tempfile
import threading
import wave
from pathlib import Path

import harumi_store

DATA = Path(os.environ.get("HARUMI_DATA", str(Path.home() / ".local/share/harumi"))) / "greeting"
RATE = 32000
JP_TEXT = "いらっしゃいませ。ようこそ。今日はどこへ行きますか。"
_lock = threading.Lock()
_pending = {"manual": False}

# Melodia original na escala "yo" (D E G A B), sem semitons: soa japonesa e alegre. (nota MIDI, duracao em batidas)
MELODY = [(74, .5), (76, .5), (79, .5), (81, 1), (79, .5), (81, .5), (83, 1.5), (81, .5), (79, .5), (76, .5), (79, 2)]
BEAT = 0.22


def _bell(freq, dur, amp=0.32):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        env = math.exp(-3.2 * t) * min(1.0, t * 200)  # ataque curto, decaimento de sino
        s = (math.sin(2 * math.pi * freq * t) + 0.35 * math.sin(2 * math.pi * freq * 2.01 * t)
             + 0.12 * math.sin(2 * math.pi * freq * 3.98 * t))
        out.append(amp * env * s / 1.47)
    return out


def jingle_bytes() -> bytes:
    total = sum(d for _, d in MELODY) * BEAT + 1.2
    buf = [0.0] * int(RATE * total)
    pos = 0.0
    for note, d in MELODY:
        f = 440.0 * 2 ** ((note - 69) / 12)
        start = int(pos * RATE)
        for i, v in enumerate(_bell(f, d * BEAT + 0.9)):
            if start + i < len(buf):
                buf[start + i] += v
        pos += d * BEAT
    peak = max(1e-9, max(abs(v) for v in buf))
    raw = b"".join(struct.pack("<h", int(max(-1, min(1, v / peak * 0.8)) * 32767)) for v in buf)
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(raw)
    return b.getvalue()


def jingle_file() -> Path:
    p = DATA / "jingle.wav"
    with _lock:
        if not p.is_file():
            DATA.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_bytes(jingle_bytes())
            os.replace(tmp, p)
    return p


def voice_file() -> Path | None:
    """Fala em japones com Open JTalk, se estiver instalado [VERIFICAR caminhos do dicionario e da voz no Ubuntu]."""
    p = DATA / "voz-ja.wav"
    if p.is_file():
        return p
    exe = shutil.which("open_jtalk")
    dic = next((d for d in ("/var/lib/mecab/dic/open-jtalk/naist-jdic",) if os.path.isdir(d)), None)
    voice = next((v for v in sorted(DATA.glob("*.htsvoice")) + sorted(Path("/usr/share/hts-voice").glob("*/*.htsvoice"))), None)
    if not (exe and dic and voice):
        return None
    DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(JP_TEXT)
        txt = f.name
    try:
        subprocess.run([exe, "-x", dic, "-m", str(voice), "-ow", str(p), txt], timeout=30, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        os.unlink(txt)
    return p if p.is_file() else None


def boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return "sem-boot-id"


def due() -> bool:
    if _pending["manual"]:
        return True
    if harumi_store.get("greeting.off", False):
        return False
    return harumi_store.get("greeting.boot") != boot_id()


def trigger():
    """Para o futuro sensor da porta: pede a saudacao na proxima consulta da tela."""
    _pending["manual"] = True


def _json(code, obj):
    return code, "application/json", json.dumps(obj, ensure_ascii=False).encode()


def _get(query):
    return _json(200, {"ok": True, "due": due(), "voz": voice_file() is not None, "off": bool(harumi_store.get("greeting.off", False)),
                       "texto": {"ja": "いらっしゃいませ！ようこそ！", "romaji": "Irasshaimase! Yōkoso!",
                                 "pt": "Seja bem-vindo, Lucas!", "pergunta": "Pra onde a gente vai hoje?"}})


def _jingle(query):
    return 200, "audio/wav", jingle_file().read_bytes()


def _voice(query):
    p = voice_file()
    if not p:
        return _json(404, {"ok": False, "erro": "sem sintetizador de voz japonesa"})
    return 200, "audio/wav", p.read_bytes()


def _done(data):
    _pending["manual"] = False
    harumi_store.set("greeting.boot", boot_id())
    return _json(200, {"ok": True})


def _test(data):
    if "off" in data:
        harumi_store.set("greeting.off", bool(data.get("off")))
        return _get(None)
    trigger()
    return _json(200, {"ok": True})


ROUTES = {"/linux/greeting": _get, "/linux/greeting-jingle": _jingle, "/linux/greeting-voice": _voice}
POST_ROUTES = {"/linux/greeting-done": _done, "/linux/greeting-test": _test}
