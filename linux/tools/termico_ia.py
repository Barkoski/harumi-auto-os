#!/usr/bin/env python3
"""Teste termico da IA: pede N respostas longas seguidas ao llama-server e registra temperatura, frequencia dos nucleos
grandes e velocidade (tokens/s, informada pelo proprio llama-server em "timings").
Uso (na placa):  python3 termico_ia.py [N=4] > resultado.json
"""
import json
import sys
import threading
import time
import urllib.request

URL = "http://127.0.0.1:8090/v1/chat/completions"
PEDIDO = ("Explique em detalhes, em uns tres paragrafos, como funciona um motor boxer de quatro cilindros, "
          "o sistema de injecao eletronica e o cambio automatico.")


def temp():
    return max(int(open(f"/sys/class/thermal/thermal_zone{i}/temp").read()) for i in range(7)) / 1000.0


def freq():
    return int(open("/sys/devices/system/cpu/cpufreq/policy4/scaling_cur_freq").read()) // 1000


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    amostras, parar = [], threading.Event()

    def amostrar():
        t0 = time.time()
        while not parar.is_set():
            amostras.append((round(time.time() - t0, 1), temp(), freq()))
            time.sleep(1)

    th = threading.Thread(target=amostrar, daemon=True)
    inicio = temp()
    th.start()
    vel = []
    for _ in range(n):
        body = json.dumps({"messages": [{"role": "user", "content": PEDIDO}], "max_tokens": 300, "temperature": 0.3,
                           "chat_template_kwargs": {"enable_thinking": False}}).encode()
        req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read())
        tm = d.get("timings") or {}
        vel.append(round(tm.get("predicted_per_second", 0), 2))
    parar.set()
    th.join()
    temps = [a[1] for a in amostras]
    print(json.dumps({"inicioC": inicio, "picoC": max(temps), "fimC": temps[-1], "duracaoS": amostras[-1][0],
                      "tokensPorSegundo": vel, "freqMHz": sorted(set(a[2] for a in amostras)),
                      "segundosAcima80": sum(1 for t in temps if t >= 80)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
