"""Modulos do carro: detecta o hardware que existe de fato na placa e devolve o estado de cada um.

Nada aqui inventa leitura: sem o hardware, o valor e None e o estado diz o que falta instalar.
  - motor (SSM1 da ECU Subaru): adaptador USB-serial em /dev/serial/by-id. A leitura do protocolo ainda nao esta
    implementada; os enderecos de memoria da ECU do EJ18 1993 precisam ser conferidos no carro [VERIFICAR].
  - bateria: medidor INA219/INA226/ADS1115 no I2C com driver do kernel (hwmon: in*_input em mV).
  - pneus (TPMS Bluetooth): exige adaptador Bluetooth; o protocolo depende do modelo do sensor [VERIFICAR modelo].
  - cameras USB (re, 360, dashcam): /sys/class/video4linux, so dispositivos USB; o papel de cada uma e escolhido na tela.
  - dashcam: grava em loop com ffmpeg (segmentos de 60 s, sobrescreve o mais antigo), so local, so quando ligada.
  - microfone: fontes do PipeWire/PulseAudio que nao sao "monitor".
  - proximidade (radar/lidar): porta serial configurada; protocolo depende do sensor [VERIFICAR modelo].
GET /linux/vehicle -> estado de todos.  POST /linux/vehicle-set {chave, valor} (papel de camera, porta) e
/linux/vehicle-dashcam {on}.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import harumi_store

DASH_DIR = Path(os.environ.get("HARUMI_DATA", str(Path.home() / ".local/share/harumi"))) / "dashcam"
DASH_SEG_S = 60
_dash = {"proc": None, "dev": None, "erro": None, "inicio": None}
_lock = threading.Lock()
ROLES = ("re", "360", "dashcam", "nenhum")


def _read(p, default=""):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return default


def serial_adapters() -> list:
    out = []
    for p in sorted(glob.glob("/dev/serial/by-id/*")):
        out.append({"id": os.path.basename(p), "dev": os.path.realpath(p)})
    return out


def cameras() -> list:
    """Cameras USB (descarta decodificadores e ISP internos do RK3588, que nao sao USB)."""
    roles = harumi_store.get("vehicle.cam_roles", {}) or {}
    out, seen = [], set()
    for d in sorted(glob.glob("/sys/class/video4linux/video*")):
        real = os.path.realpath(d)
        if "/usb" not in real:
            continue
        name = _read(os.path.join(d, "name"), "camera")
        usbdev = real.split("/video4linux/")[0]
        if usbdev in seen:  # uma camera USB costuma criar 2 nos (video + metadados): fica com o primeiro
            continue
        seen.add(usbdev)
        dev = "/dev/" + os.path.basename(d)
        out.append({"dev": dev, "nome": name[:60], "papel": roles.get(name[:60], "nenhum")})
    return out


def battery() -> dict:
    for h in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        name = _read(os.path.join(h, "name"))
        if not any(k in name for k in ("ina2", "ina3", "ads1", "ads7")):
            continue
        # INA2xx: in1 = tensao do barramento (mV). ADS1x15: canal escolhido em vehicle.bat_channel e divisor em
        # vehicle.bat_div (o divisor resistivo e montado por voce; sem ele o ADS nao aguenta 12 V).
        chan = harumi_store.get("vehicle.bat_channel", "in1_input" if name.startswith("ina") else "in4_input")
        div = harumi_store.get("vehicle.bat_div", 1.0)
        raw = _read(os.path.join(h, str(chan)))
        try:
            v = int(raw) / 1000.0 * float(div)
        except (ValueError, TypeError):
            return {"estado": "erro", "sensor": name, "volts": None, "detalhe": "leitura invalida em " + str(chan)}
        estado = "ok" if 12.2 <= v <= 14.8 else ("baixa" if v < 12.2 else "alta")
        return {"estado": estado, "sensor": name, "volts": round(v, 2)}
    return {"estado": "nao_instalado", "sensor": None, "volts": None}


def bluetooth() -> bool:
    return bool(glob.glob("/sys/class/bluetooth/hci*"))


def microphones() -> list:
    try:
        r = subprocess.run(["pactl", "list", "short", "sources"], capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.SubprocessError):
        return []
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) > 1 and ".monitor" not in parts[1]:
            out.append(parts[1][:80])
    return out


def dash_state() -> dict:
    with _lock:
        p = _dash["proc"]
        rec = bool(p and p.poll() is None)
        if p and not rec and not _dash["erro"]:
            _dash["erro"] = "a gravação parou (código %s)" % p.returncode
        files = sorted(DASH_DIR.glob("seg*.mp4")) if DASH_DIR.is_dir() else []
        used = sum(f.stat().st_size for f in files)
        return {"gravando": rec, "dev": _dash["dev"] if rec else None, "erro": _dash["erro"],
                "desde": _dash["inicio"] if rec else None, "arquivos": len(files), "usadoMB": round(used / 1e6, 1),
                "limiteGB": harumi_store.get("vehicle.dash_gb", 8), "ffmpeg": bool(shutil.which("ffmpeg"))}


def dash_start() -> str | None:
    cam = next((c for c in cameras() if c["papel"] == "dashcam"), None)
    if not cam:
        return "Escolha qual câmera é a dashcam."
    if not shutil.which("ffmpeg"):
        return "ffmpeg não está instalado."
    gb = harumi_store.get("vehicle.dash_gb", 8)
    # ~8 MB por minuto em 720p com libx264 ultrafast/crf 28 (estimativa; ajusta o numero de segmentos ao limite)
    wrap = max(10, int(float(gb) * 1000 / 8))
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "v4l2", "-video_size", "1280x720", "-i", cam["dev"],
           "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-f", "segment",
           "-segment_time", str(DASH_SEG_S), "-segment_wrap", str(wrap), "-reset_timestamps", "1",
           str(DASH_DIR / "seg%04d.mp4")]
    with _lock:
        if _dash["proc"] and _dash["proc"].poll() is None:
            return None
        try:
            _dash["proc"] = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as e:
            return "Não consegui iniciar: " + str(e)[:80]
        _dash.update(dev=cam["dev"], erro=None, inicio=int(time.time()))
    return None


def dash_stop():
    with _lock:
        p = _dash["proc"]
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(5)
            except subprocess.TimeoutExpired:
                p.kill()
        _dash["proc"] = None


def state() -> dict:
    ser = serial_adapters()
    ssm_port = harumi_store.get("vehicle.ssm1_port")
    radar_port = harumi_store.get("vehicle.radar_port")
    cams = cameras()
    mics = microphones()
    bt = bluetooth()

    def port_state(port):
        if port and any(s["id"] == port for s in ser):
            return "conectado"
        return "detectado" if ser else "nao_instalado"

    return {
        "ok": True,
        "motor": {"estado": port_state(ssm_port), "porta": ssm_port, "rpm": None, "aguaC": None, "kmh": None,
                  "nota": "Leitura SSM1 ainda não validada no carro." if ser else "Instale o cabo SSM1 (USB-serial 5 V)."},
        "bateria": battery(),
        "pneus": {"estado": "aguardando_sensores" if bt else "sem_bluetooth", "pneus": None,
                  "nota": "Escolha o modelo dos sensores BLE para ativar." if bt else "Precisa de adaptador Bluetooth."},
        "cameras": cams,
        "dashcam": dash_state(),
        "microfone": {"estado": "ok" if mics else "nao_instalado", "fontes": mics[:6]},
        "proximidade": {"estado": port_state(radar_port), "porta": radar_port, "setores": None,
                        "nota": "Instale o radar/sensor de ré e escolha a porta."},
        "seriais": ser,
    }


def _json(code, obj):
    return code, "application/json", json.dumps(obj, ensure_ascii=False).encode()


def _get(query):
    return _json(200, state())


def _set(data):
    key, val = data.get("chave"), data.get("valor")
    if key == "cam_role":
        nome, papel = str((val or {}).get("nome", ""))[:60], (val or {}).get("papel")
        if not nome or papel not in ROLES:
            return _json(400, {"ok": False, "erro": "papel inválido"})
        roles = harumi_store.get("vehicle.cam_roles", {}) or {}
        if papel != "nenhum":  # um papel por camera
            roles = {k: v for k, v in roles.items() if v != papel}
        roles[nome] = papel
        harumi_store.set("vehicle.cam_roles", roles)
    elif key in ("ssm1_port", "radar_port"):
        if val is not None and not any(s["id"] == val for s in serial_adapters()):
            return _json(400, {"ok": False, "erro": "porta não encontrada"})
        harumi_store.set("vehicle." + key, val)
    elif key == "dash_gb":
        try:
            gb = float(val)
        except (TypeError, ValueError):
            return _json(400, {"ok": False, "erro": "número inválido"})
        if not 1 <= gb <= 200:
            return _json(400, {"ok": False, "erro": "entre 1 e 200 GB"})
        harumi_store.set("vehicle.dash_gb", gb)
    else:
        return _json(400, {"ok": False, "erro": "chave desconhecida"})
    return _json(200, state())


def _dashcam(data):
    if data.get("on"):
        err = dash_start()
        if err:
            return _json(400, {"ok": False, "erro": err})
    else:
        dash_stop()
    return _json(200, state())


ROUTES = {"/linux/vehicle": _get}
POST_ROUTES = {"/linux/vehicle-set": _set, "/linux/vehicle-dashcam": _dashcam}
