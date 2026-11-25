#!/usr/bin/env python3
"""Ferramenta de bancada: fala com o Chromium do quiosque pelo DevTools (127.0.0.1:9222), so biblioteca padrao.

  python3 cdp.py shot saida.png          captura a tela da Harumi
  python3 cdp.py eval "expressao JS"     avalia JS na pagina e imprime o resultado
  python3 cdp.py console                 mostra erros recentes do console (5 s)
"""
import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request


def target():
    pages = json.load(urllib.request.urlopen("http://127.0.0.1:" + os.environ.get("CDP_PORT", "9222") + "/json"))
    pages = [p for p in pages if p.get("type") == "page"]
    want = os.environ.get("CDP_MATCH", "127.0.0.1:8765")  # a Harumi; CDP_MATCH=youtube.com pega o app embutido
    pages = [p for p in pages if want in p.get("url", "")] or pages
    if not pages:
        sys.exit("nenhuma pagina aberta no Chromium")
    return pages[0]["webSocketDebuggerUrl"]


class WS:
    def __init__(self, url):
        rest = url.split("://", 1)[1]
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.s = socket.create_connection((host, int(port)), timeout=20)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.extra = buf.split(b"\r\n\r\n", 1)[1]
        self.n = 0

    def _recv(self, n):
        while len(self.extra) < n:
            chunk = self.s.recv(1 << 16)
            if not chunk:
                raise EOFError
            self.extra += chunk
        out, self.extra = self.extra[:n], self.extra[n:]
        return out

    def send(self, method, params=None):
        self.n += 1
        data = json.dumps({"id": self.n, "method": method, "params": params or {}}).encode()
        mask = os.urandom(4)
        head = bytes([0x81])
        ln = len(data)
        head += bytes([0x80 | ln]) if ln < 126 else (bytes([0x80 | 126]) + struct.pack(">H", ln) if ln < 65536 else bytes([0x80 | 127]) + struct.pack(">Q", ln))
        self.s.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        return self.n

    def recv(self):
        payload = b""
        while True:
            b1, b2 = self._recv(2)
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._recv(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._recv(8))[0]
            payload += self._recv(ln)
            if b1 & 0x80:
                return json.loads(payload)

    def call(self, method, params=None):
        mid = self.send(method, params)
        while True:
            m = self.recv()
            if m.get("id") == mid:
                return m


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "shot"
    ws = WS(target())
    if cmd == "shot":
        r = ws.call("Page.captureScreenshot", {"format": "png"})
        open(sys.argv[2] if len(sys.argv) > 2 else "shot.png", "wb").write(base64.b64decode(r["result"]["data"]))
        print("ok")
    elif cmd == "eval":
        r = ws.call("Runtime.evaluate", {"expression": sys.argv[2], "returnByValue": True, "awaitPromise": True})
        print(json.dumps(r.get("result", {}).get("result", {}).get("value"), ensure_ascii=False))
    elif cmd == "console":
        ws.call("Runtime.enable")
        ws.call("Log.enable")
        end = time.time() + 5
        ws.s.settimeout(1)
        while time.time() < end:
            try:
                m = ws.recv()
            except (socket.timeout, EOFError):
                continue
            if m.get("method") in ("Runtime.exceptionThrown", "Log.entryAdded", "Runtime.consoleAPICalled"):
                print(json.dumps(m["params"], ensure_ascii=False)[:400])


if __name__ == "__main__":
    main()
