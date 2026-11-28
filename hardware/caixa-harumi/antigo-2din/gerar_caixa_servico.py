#!/usr/bin/env python3
"""Gera os STLs da caixinha de servico da Harumi: hub USB 7 portas, modem 4G, optoacoplador PC817 e rele ACC.

Fica atras do painel ou no porta-luvas, ligada a caixa 2-DIN por um cabo USB 3.0 curto.
Usa o mesmo motor de voxels do gerar_caixa.py (Grid, write_stl).

Uso:  python gerar_caixa_servico.py   -> grava 6_caixa_servico.stl e 7_tampa_servico.stl nesta pasta
Eixos: x = comprimento, y = altura (0 = fundo), z = largura. Unidade: mm.
Medidas das pecas (fontes no LEIA-ME):
  hub ORICO 7 portas 145 x 58 x 26 (portas em cima)   modem Huawei E3372h 88 x 28 x 11,5
  PC817 4 canais ~40 x 30 x 15 [estimado]             rele temporizador ACC ~50 x 26 x 18 [estimado]
[VERIFICAR] medir o hub e os modulos que chegarem e o espaco do porta-luvas antes de imprimir.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerar_caixa import RES, Grid, write_stl  # noqa: E402

PAREDE = 2.5
INT_L, INT_A, INT_P = 175.0, 70.0, 128.0      # interno: comprimento x altura x largura
EXT_L, EXT_A, EXT_P = INT_L + 2 * PAREDE, INT_A + PAREDE, INT_P + 2 * PAREDE   # aberta em cima
COL = 8.0                                      # colunas dos parafusos da tampa (M3 auto-atarraxante)
COLS = [(PAREDE + COL / 2, PAREDE + COL / 2), (EXT_L - PAREDE - COL / 2, PAREDE + COL / 2),
        (PAREDE + COL / 2, EXT_P - PAREDE - COL / 2), (EXT_L - PAREDE - COL / 2, EXT_P - PAREDE - COL / 2)]

# Posicoes das pecas no fundo (x0, x1, z0, z1), usadas para as fendas de abracadeira
HUB = (PAREDE + 22, PAREDE + 22 + 145, PAREDE + 1, PAREDE + 1 + 58)    # 22 mm a esquerda para o plugue da fonte
MODEM = (PAREDE + 10, PAREDE + 10 + 88, PAREDE + 64, PAREDE + 64 + 28)
PC817 = (PAREDE + 104, PAREDE + 104 + 40, PAREDE + 64, PAREDE + 64 + 30)
RELE = (PAREDE + 10, PAREDE + 10 + 50, PAREDE + 99, PAREDE + 99 + 26)


def caixa():
    g = Grid(-14, EXT_L + 14, 0, EXT_A, 0, EXT_P)
    g.box(0, EXT_L, 0, EXT_A, 0, EXT_P)
    g.box(PAREDE, EXT_L - PAREDE, PAREDE, EXT_A + 1, PAREDE, EXT_P - PAREDE, False)
    for (x, z) in COLS:                                   # colunas com furo de 2,8 mm (M3 auto-atarraxante)
        g.box(x - COL / 2, x + COL / 2, 0, EXT_A, z - COL / 2, z + COL / 2)
        g.cyl(1, x, z, 1.4, EXT_A - 14, EXT_A + 1, False)
    for x0 in (-12, EXT_L):                               # orelhas de fixacao com furo M4
        for zc in (30, EXT_P - 30):
            g.box(x0, x0 + 12, 0, 4, zc - 12, zc + 12)
            g.cyl(1, x0 + 6, zc, 2.2, -1, 5, False)
    for x in (30, 60, 90, 120):                           # passa-fios de 14 mm na parede de tras (12 V, ACC, sinais)
        g.cyl(2, x, 40, 7.0, EXT_P - PAREDE - 1, EXT_P + 1, False)
    g.cyl(2, 150, 40, 7.0, -1, PAREDE + 1, False)         # cabo USB 3.0 para a caixa 2-DIN (parede da frente)
    g.cyl(0, 45, PAREDE + 30, 7.0, -1, PAREDE + 1, False) # lateral esquerda: fonte do hub ou extensor da antena
    for (x0, x1, z0, z1) in (HUB, MODEM, PC817, RELE):    # pares de fendas para abracadeira de 3 mm
        for x in (x0 + 8, x1 - 12):
            for z in (z0 - 4, z1 + 1):
                if PAREDE < z < EXT_P - PAREDE - 3:
                    g.box(x, x + 4, -1, PAREDE + 1, z, z + 3, False)
    for i in range(10):                                   # furos de ar no fundo, sob o hub
        g.cyl(1, HUB[0] + 12 + i * 13, (HUB[2] + HUB[3]) / 2, 2.5, -1, PAREDE + 1, False)
    return g


def tampa():
    t = 2.5
    g = Grid(0, EXT_L, 0, t, 0, EXT_P)
    g.box(0, EXT_L, 0, t, 0, EXT_P)
    for (x, z) in COLS:
        g.cyl(1, x, z, 1.7, -1, t + 1, False)
    for i in range(9):                                    # grade de ar sobre o hub
        x = HUB[0] + 8 + i * 15
        g.box(x, x + 4, -1, t + 1, HUB[2] + 8, HUB[3] - 8, False)
    return g


PECAS = [("6_caixa_servico", caixa), ("7_tampa_servico", tampa)]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for name, fn in PECAS:
        g = fn()
        tris = g.mesh()
        n, vol = write_stl(os.path.join(here, name + ".stl"), tris, "Harumi " + name)
        vox = float(g.v.sum()) * RES ** 3
        ok = abs(vol - vox) / vox < 1e-3
        dims = g.n * RES
        print(f"{name}: {n} triangulos, {dims[0]:.0f} x {dims[1]:.0f} x {dims[2]:.0f} mm, "
              f"volume {vol / 1000:.1f} cm3 (voxels {vox / 1000:.1f}) {'OK' if ok else 'ERRO'}", flush=True)
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
