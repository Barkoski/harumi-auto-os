#!/usr/bin/env python3
"""Governador termico da Harumi (roda como root, servico harumi-cpufreq).

Em vez de desligar a IA quando a placa esquenta, baixa a frequencia maxima dos nucleos grandes (A76, onde roda a IA)
em degraus, com folga para nao ficar oscilando. Medicao de 20/11/2026: o chip pula de 50 para 63 C em 2 s quando a IA
comeca a responder e passou de 80 C numa resposta longa, ja com caixa, ventoinha e dissipadores.

Degraus (temperatura da maior zona termica -> teto dos nucleos grandes):
  abaixo de 70 C: TETO_NORMAL (padrao 1800 MHz; o maximo de fabrica e 2400)
  70 C ou mais:   1608 MHz
  76 C ou mais:   1416 MHz
  82 C ou mais:   1200 MHz
Teste A/B de 20/11/2026 (4 respostas longas seguidas): sem governador pico 89,4 C e 86 s acima de 80 C; com 2016 MHz e
degraus 72/78/84, pico 85 C e 43 s acima de 80 C, com a mesma velocidade (~13 tokens/s: a IA e limitada pela memoria).
Para subir de volta um degrau, a temperatura precisa ficar FOLGA (4 C) abaixo do limite daquele degrau.
A pausa da IA (plugins/thermal.py, usuario) fica so como ultima defesa, a 88 C.

Configuracao opcional em /etc/default/harumi-cpufreq:  TETO_NORMAL=2400  (volta ao maximo de fabrica)
Estado atual: /run/harumi-cpufreq.json  {tempC, tetoMHz, degrau}
Desfazer: sudo systemctl disable --now harumi-cpufreq  (o servico devolve o teto de fabrica ao parar)
"""
import glob
import json
import os
import signal
import sys
import time

POLICIES = ["/sys/devices/system/cpu/cpufreq/policy4", "/sys/devices/system/cpu/cpufreq/policy6"]
DEGRAUS = [(82, 1200000), (76, 1416000), (70, 1608000)]  # do mais quente para o mais frio
FOLGA = 4
INTERVALO = 2.0
ESTADO = "/run/harumi-cpufreq.json"


def ler_config():
    teto = 1800000
    try:
        for linha in open("/etc/default/harumi-cpufreq", encoding="utf-8"):
            k, _, v = linha.strip().partition("=")
            if k == "TETO_NORMAL" and v.strip().isdigit():
                teto = int(v.strip()) * 1000
    except OSError:
        pass
    return teto


def disponiveis(pol):
    try:
        return sorted(int(x) for x in open(pol + "/scaling_available_frequencies").read().split())
    except (OSError, ValueError):
        return []


def ajustar(teto_khz):
    for pol in POLICIES:
        freqs = disponiveis(pol)
        if not freqs:
            continue
        alvo = max([f for f in freqs if f <= teto_khz] or [freqs[0]])
        try:
            atual = int(open(pol + "/scaling_max_freq").read())
            if atual != alvo:
                with open(pol + "/scaling_max_freq", "w") as f:
                    f.write(str(alvo))
        except (OSError, ValueError):
            pass


def temperatura():
    maior = None
    for z in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            t = int(open(z).read()) / 1000.0
        except (OSError, ValueError):
            continue
        if 0 < t < 150 and (maior is None or t > maior):
            maior = t
    return maior


def degrau_para(temp, atual):
    """atual = indice em DEGRAUS (len(DEGRAUS) = normal). Sobe rapido, desce com folga."""
    novo = len(DEGRAUS)
    for i, (lim, _) in enumerate(DEGRAUS):
        if temp >= lim:
            novo = i
            break
    if novo > atual:  # esfriou: so libera um degrau por vez e com folga
        lim_atual = DEGRAUS[atual][0] if atual < len(DEGRAUS) else 0
        return atual + 1 if temp <= lim_atual - FOLGA else atual
    return novo


def restaurar(*_):
    for pol in POLICIES:
        freqs = disponiveis(pol)
        if freqs:
            try:
                with open(pol + "/scaling_max_freq", "w") as f:
                    f.write(str(freqs[-1]))
            except OSError:
                pass
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, restaurar)
    signal.signal(signal.SIGINT, restaurar)
    teto_normal = ler_config()
    nivel = len(DEGRAUS)
    while True:
        t = temperatura()
        if t is not None:
            nivel = degrau_para(t, nivel)
        teto = DEGRAUS[nivel][1] if nivel < len(DEGRAUS) else teto_normal
        teto = min(teto, teto_normal)
        ajustar(teto)
        try:
            tmp = ESTADO + ".tmp"
            with open(tmp, "w") as f:
                json.dump({"tempC": t, "tetoMHz": teto // 1000, "degrau": len(DEGRAUS) - nivel}, f)
            os.replace(tmp, ESTADO)
        except OSError:
            pass
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
