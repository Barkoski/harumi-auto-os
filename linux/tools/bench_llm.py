#!/usr/bin/env python3
"""Bancada de IA local no Orange Pi: mede velocidade, RAM, temperatura e coleta respostas em portugues.

Para cada modelo: sobe o llama-server preso aos 4 nucleos grandes (A76), faz as mesmas perguntas
(sem modo de raciocinio) e grava tudo em ~/harumi/llm/resultado.json.
"""
import glob
import json
import os
import subprocess
import time
import urllib.request

L = os.path.expanduser("~/harumi/llm")
BIN = f"{L}/llama.cpp/build/bin"
PORT = 8090
SYSTEM = ("Você é a Harumi, assistente de voz de um Subaru Impreza 1993. Responda em português do Brasil, "
          "curto e claro, como quem fala com o motorista. Se não souber, diga que não sabe.")
PROMPTS = [
    ("luz_oleo", "A luz de óleo acendeu no painel enquanto eu dirijo. O que eu faço? Responda em no máximo duas frases."),
    ("intencao_json", "Transforme o pedido em JSON com as chaves acao e destino, sem explicar nada: "
                      "\"me leva pro shopping catuaí em londrina\""),
    ("conforto", "Tá muito quente aqui dentro."),
    ("resumo_rota", "Resuma para o motorista em uma frase: rota de 100 km, 1 hora e 28 minutos, passando por Arapongas e Mandaguari."),
    ("fora_escopo", "Qual foi o placar do último jogo do Londrina?"),
]


def temp_c():
    vals = []
    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            vals.append(int(open(f).read()) / 1000)
        except (OSError, ValueError):
            pass
    return max(vals) if vals else None


def rss_mb(pid):
    try:
        for line in open(f"/proc/{pid}/status"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) // 1024
    except OSError:
        return None


def post(path, body, timeout=600):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def wait_ready(proc, limit=180):
    t0 = time.time()
    while time.time() - t0 < limit:
        if proc.poll() is not None:
            raise RuntimeError("llama-server saiu")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if r.status == 200:
                    return time.time() - t0
        except OSError:
            pass
        time.sleep(0.5)
    raise RuntimeError("llama-server nao ficou pronto")


def run_model(path):
    name = os.path.basename(path)
    cmd = ["taskset", "-c", "4-7", f"{BIN}/llama-server", "-m", path, "-t", "4", "-c", "4096",
           "--host", "127.0.0.1", "--port", str(PORT), "--no-webui"]
    log = open(f"{L}/server-{name}.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    res = {"model": name, "size_mb": os.path.getsize(path) // 1_000_000, "answers": []}
    try:
        res["load_s"] = round(wait_ready(proc), 1)
        res["temp_start_c"] = temp_c()
        for key, prompt in PROMPTS:
            t0 = time.time()
            j = post("/v1/chat/completions", {
                "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                "max_tokens": 160, "temperature": 0.3, "chat_template_kwargs": {"enable_thinking": False}})
            t = j.get("timings", {})
            res["answers"].append({
                "id": key, "wall_s": round(time.time() - t0, 2),
                "prompt_tok": t.get("prompt_n"), "prompt_tps": round(t.get("prompt_per_second", 0), 1),
                "gen_tok": t.get("predicted_n"), "gen_tps": round(t.get("predicted_per_second", 0), 1),
                "text": j["choices"][0]["message"].get("content", "").strip()})
        res["rss_mb"] = rss_mb(proc.pid)
        res["temp_end_c"] = temp_c()
    except Exception as e:  # registra e segue para o proximo modelo
        res["error"] = repr(e)
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
    return res


def main():
    models = sorted(glob.glob(f"{L}/models/*.gguf"), key=os.path.getsize)
    out = {"date": time.strftime("%Y-%m-%d %H:%M"), "threads": "4 (A76, nucleos 4-7)", "results": []}
    for m in models:
        print("testando", m, flush=True)
        out["results"].append(run_model(m))
        json.dump(out, open(f"{L}/resultado.json", "w"), ensure_ascii=False, indent=1)
        time.sleep(20)  # esfria entre modelos
    print("ok", flush=True)


if __name__ == "__main__":
    main()
