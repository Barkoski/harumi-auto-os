#!/usr/bin/env python3
"""Controle do PC de casa a partir do Orange Pi (para quando o Lucas estiver viajando).

- Liga o PC por Wake-on-LAN (pacote magico na placa de rede COM FIO do PC).
- Mostra se o PC esta ligado (ping).
- Pagina web simples com os botoes, para abrir pelo celular via Tailscale: http://<ip-tailscale-do-pi>:8099

Uso:
  python3 controle_pc.py acordar        # manda o pacote magico
  python3 controle_pc.py status         # diz se o PC responde
  python3 controle_pc.py servidor       # sobe a pagina na porta 8099 (so escuta no Tailscale e na rede local)
Sem dependencias alem do Python 3.
"""
import html
import http.server
import socket
import subprocess
import sys
import time

import configparser
import os

# Dados da rede de casa ficam FORA do codigo, em ~/.config/harumi/pc.conf:
#   [pc]
#   mac = AA:BB:CC:DD:EE:FF        (placa de rede COM FIO do PC)
#   ip = 192.168.0.X
#   broadcast = 192.168.0.255
_conf = configparser.ConfigParser()
_conf.read(os.path.expanduser("~/.config/harumi/pc.conf"))
PC_MAC = _conf.get("pc", "mac", fallback="00:00:00:00:00:00")
PC_IP = _conf.get("pc", "ip", fallback="192.168.0.2")
BROADCAST = _conf.get("pc", "broadcast", fallback="192.168.0.255")
PORTA = 8099


def acordar():
    mac = bytes.fromhex(PC_MAC.replace(":", ""))
    pacote = b"\xff" * 6 + mac * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for _ in range(3):                                   # manda 3 vezes, nas portas 9 e 7
            for porta in (9, 7):
                s.sendto(pacote, (BROADCAST, porta))
            time.sleep(0.2)
    return "Pacote para ligar o PC enviado. Ele leva cerca de 1 minuto para aparecer como ligado."


def ligado():
    r = subprocess.run(["ping", "-c", "1", "-W", "1", PC_IP], capture_output=True)
    return r.returncode == 0


PAGINA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PC de casa</title><style>
body{{font:17px system-ui,sans-serif;background:#1f262b;color:#dde4e9;margin:0;padding:24px 16px;display:grid;gap:16px;max-width:420px}}
h1{{font-size:22px;margin:0}} .st{{padding:12px;border-radius:8px;background:#2a3238}} .on{{color:#79b98a}} .off{{color:#d99a5f}}
button{{font:inherit;font-weight:600;padding:16px;border:0;border-radius:8px;background:#6fb0cf;color:#10181d;width:100%}}
button:focus-visible{{outline:3px solid #fff}} p{{margin:0;color:#97a4ad;font-size:14px}}
</style></head><body><h1>PC de casa</h1>
<div class="st">Estado: <b class="{cls}">{estado}</b></div>
<form method="post" action="/acordar"><button>Ligar o PC</button></form>
{msg}
<p>Para desligar: abra o Claude no celular e peça na sessão do PC, ou use o botão Iniciar do Windows pela área de trabalho remota.</p>
</body></html>"""


class Pagina(http.server.BaseHTTPRequestHandler):
    def _render(self, msg=""):
        on = ligado()
        corpo = PAGINA.format(cls="on" if on else "off", estado="ligado" if on else "desligado (ou sem resposta)",
                              msg=f"<p>{html.escape(msg)}</p>" if msg else "").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        self._render()

    def do_POST(self):
        if self.path == "/acordar":
            self._render(acordar())
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass


def servidor():
    http.server.ThreadingHTTPServer(("0.0.0.0", PORTA), Pagina).serve_forever()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "acordar":
        print(acordar())
    elif cmd == "servidor":
        servidor()
    else:
        print("PC ligado" if ligado() else "PC desligado ou sem resposta")
