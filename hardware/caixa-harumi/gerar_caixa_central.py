#!/usr/bin/env python3
"""Gera os STLs da caixa da central da Harumi (plano de 20/11/2026: tela de 10,1" em cima do painel, sem caixa 2-DIN).

Uma caixa so, embaixo do painel do lado do passageiro (fora do porta-luvas fechado, para pegar ar da cabine), com:
  Orange Pi 5 + case com fan, conversor 12->5 V 10 A, hub USB 7 portas (com Bluetooth, FT232RL e captura plugados),
  modem 4G deitado, optoacoplador PC817 e rele temporizador ACC. Ventoinha Noctua 40 mm na tampa, sobre o Orange Pi.

Uso:  python gerar_caixa_central.py   -> grava 6_caixa_central.stl, 7_tampa_central.stl e 8_bocal_ar_condicionado.stl
Eixos: x = comprimento, y = altura (0 = fundo), z = largura (0 = parede da frente, a dos cabos da tela). mm.
Pecas (fontes no LEIA-ME):  Orange Pi 5 100 x 62 (case ~104 x 66 x 24 est.)  conversor 66 x 60 x 22
  hub ORICO 145 x 58 x 26   modem 88 x 28 x 11,5   PC817 ~40 x 30 x 15 est.   rele ~50 x 26 x 18 est.
[VERIFICAR] medir as pecas que chegarem e o espaco embaixo do painel do passageiro antes de imprimir.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerar_caixa import RES, Grid, write_stl  # noqa: E402

PAREDE = 2.5
INT_L, INT_A, INT_P = 200.0, 70.0, 190.0
EXT_L, EXT_A, EXT_P = INT_L + 2 * PAREDE, INT_A + PAREDE, INT_P + 2 * PAREDE   # aberta em cima
COL = 8.0
COLS = [(PAREDE + COL / 2, PAREDE + COL / 2), (EXT_L - PAREDE - COL / 2, PAREDE + COL / 2),
        (PAREDE + COL / 2, EXT_P - PAREDE - COL / 2), (EXT_L - PAREDE - COL / 2, EXT_P - PAREDE - COL / 2)]


def _p(x0, w, z0, d):
    return (PAREDE + x0, PAREDE + x0 + w, PAREDE + z0, PAREDE + z0 + d)


# Posicoes no fundo (x0, x1, z0, z1). Fileira A: Orange Pi (conectores HDMI/USB-C virados para a parede da frente,
# 20 mm de folga para plugues em 90 graus; USB e rede virados para a esquerda, 20 mm) e conversor.
OPI = _p(20, 104, 20, 66)
CONV = _p(130, 66, 23, 60)
HUB = _p(26, 145, 92, 58)             # 26 mm a esquerda para o plugue da fonte do hub
MODEM = _p(6, 88, 152, 28)
PC817 = _p(96, 40, 152, 28)
RELE = _p(140, 50, 154, 26)
# Ventilacao "empurra e puxa" (ideia do Lucas, 20/11/2026): 2 ventoinhas de 80 mm por fora da tampa.
# ENTRADA sobre o Orange Pi (ar frio da cabine ou do ar-condicionado pelo bocal) e SAIDA no canto oposto.
FAN_80, FAN_80_FURO = 80.0, 71.5                                  # ventoinha 80 mm, furos a 71,5 mm
FAN = (OPI[0] + OPI[1]) / 2, (OPI[2] + OPI[3]) / 2               # entrada: sobre o Orange Pi
FAN_SAIDA = (EXT_L - PAREDE - 55.0, EXT_P - PAREDE - 55.0)        # saida: canto oposto (sobre modem/rele/hub)


def caixa():
    g = Grid(-14, EXT_L + 14, 0, EXT_A, 0, EXT_P)
    g.box(0, EXT_L, 0, EXT_A, 0, EXT_P)
    g.box(PAREDE, EXT_L - PAREDE, PAREDE, EXT_A + 1, PAREDE, EXT_P - PAREDE, False)
    for (x, z) in COLS:
        g.box(x - COL / 2, x + COL / 2, 0, EXT_A, z - COL / 2, z + COL / 2)
        g.cyl(1, x, z, 1.4, EXT_A - 14, EXT_A + 1, False)
    for x0 in (-12, EXT_L):                                       # orelhas M4
        for zc in (35, EXT_P - 35):
            g.box(x0, x0 + 12, 0, 4, zc - 12, zc + 12)
            g.cyl(1, x0 + 6, zc, 2.2, -1, 5, False)
    for x in (45, 95):                                            # frente: cabo HDMI e USB do touch (passa o plugue)
        g.cyl(2, x, 40, 12.5, -1, PAREDE + 1, False)
    for x in (30, 62, 94, 126, 158, 190):                         # tras: 12 V, ACC, sinais, GPS, mic, video, nos
        g.cyl(2, x, 40, 11.0, EXT_P - PAREDE - 1, EXT_P + 1, False)
    for (x0, x1, z0, z1) in (OPI, CONV, HUB, MODEM, PC817, RELE):  # fendas de abracadeira
        for x in (x0 + 8, x1 - 12):
            for z in (z0 - 4, z1 + 1):
                if PAREDE < z < EXT_P - PAREDE - 3:
                    g.box(x, x + 4, -1, PAREDE + 1, z, z + 3, False)
    for i in range(6):                                            # ar por baixo do Orange Pi
        for j in range(3):
            g.cyl(1, OPI[0] + 14 + i * 15, OPI[2] + 15 + j * 18, 2.5, -1, PAREDE + 1, False)
    return g


def _furo_fan(g, fx, fz, t):
    """Abertura de uma ventoinha de 80 mm: furo de 76 mm com grade (anel + cruz) e 4 furos M4 auto-atarraxantes."""
    g.cyl(1, fx, fz, 38.0, -1, t + 1, False)
    g.cyl(1, fx, fz, 14.0, 0, t)
    g.cyl(1, fx, fz, 12.0, -1, t + 1, False)
    g.cyl(1, fx, fz, 27.0, 0, t)
    g.cyl(1, fx, fz, 25.0, -1, t + 1, False)
    g.box(fx - 1.2, fx + 1.2, 0, t, fz - 38, fz + 38)
    g.box(fx - 38, fx + 38, 0, t, fz - 1.2, fz + 1.2)
    for dx in (-FAN_80_FURO / 2, FAN_80_FURO / 2):
        for dz in (-FAN_80_FURO / 2, FAN_80_FURO / 2):
            g.cyl(1, fx + dx, fz + dz, 2.0, -1, t + 1, False)


def tampa():
    """Tampa com 2 ventoinhas de 80 mm montadas por fora: entrada sobre o Orange Pi, saida no canto oposto.
    O ar atravessa a caixa inteira; os passa-fios devem ficar vedados com borracha para o fluxo nao escapar."""
    t = 3.0
    g = Grid(0, EXT_L, 0, t, 0, EXT_P)
    g.box(0, EXT_L, 0, t, 0, EXT_P)
    for (x, z) in COLS:
        g.cyl(1, x, z, 1.7, -1, t + 1, False)
    _furo_fan(g, *FAN, t)
    _furo_fan(g, *FAN_SAIDA, t)
    return g


def bocal():
    """Bocal opcional: encaixa sobre a ventoinha de ENTRADA e recebe uma mangueira de 50 mm vinda da saida de ar do
    passageiro (ar-condicionado). Placa 80 x 80 com os 4 furos, funil e ponta de 50 mm para abracadeira."""
    g = Grid(0, FAN_80, 0, 66, 0, FAN_80)
    c = FAN_80 / 2
    g.box(0, FAN_80, 0, 3, 0, FAN_80)
    g.cyl(1, c, c, 37.0, -1, 4, False)
    for dx in (-FAN_80_FURO / 2, FAN_80_FURO / 2):
        for dz in (-FAN_80_FURO / 2, FAN_80_FURO / 2):
            g.cyl(1, c + dx, c + dz, 2.2, -1, 4, False)
    for k in range(10):                                           # funil de 80 para 50 mm em degraus de 3 mm
        y0 = 3 + 3 * k
        r_ext = 39.5 - k * 1.45
        g.cyl(1, c, c, r_ext, y0, y0 + 3)
        g.cyl(1, c, c, r_ext - 2.5, y0 - 0.01, y0 + 3.01, False)
    g.cyl(1, c, c, 25.0, 33, 66)                                  # ponta para mangueira de 50 mm (diametro interno)
    g.cyl(1, c, c, 22.5, 32.9, 67, False)
    g.cyl(1, c, c, 26.5, 60, 63)                                  # anel para a mangueira nao escapar
    g.cyl(1, c, c, 22.5, 59.9, 63.1, False)
    return g


def capuz_saida():
    """Capuz da SAIDA de ar: encaixa sobre a ventoinha de saida e vira o ar quente 90 graus, para a cabine (lado do
    banco), em vez de soprar para cima, onde ele ficaria preso atras do porta-luvas. Saida de 76 x 32 mm com aba que
    aponta o ar para baixo (pe do passageiro fica de lado). Opcional: ponta redonda de 50 mm para mangueira."""
    t, alt = 2.5, 40.0
    g = Grid(0, FAN_80, 0, alt + t + 12, -14, FAN_80)
    c = FAN_80 / 2
    g.box(0, FAN_80, 0, 3, 0, FAN_80)                                  # placa com os 4 furos
    g.cyl(1, c, c, 37.0, -1, 4, False)
    for dx in (-FAN_80_FURO / 2, FAN_80_FURO / 2):
        for dz in (-FAN_80_FURO / 2, FAN_80_FURO / 2):
            g.cyl(1, c + dx, c + dz, 2.2, -1, 4, False)
    g.box(0, FAN_80, 3, alt + t, 0, FAN_80)                            # camara
    g.box(t, FAN_80 - t, 2.9, alt, t, FAN_80 - t, False)
    g.box(t, FAN_80 - t, 5, alt - 3, -1, t + 0.01, False)              # boca virada para z = 0 (cabine)
    for i in range(4):                                                 # aba em degraus apontando o ar para baixo
        g.box(t, FAN_80 - t, alt - 3 - i * 2, alt + t - i * 2, -3 - i * 3, 0)
    return g


PECAS = [("6_caixa_central", caixa), ("7_tampa_central", tampa), ("8_bocal_ar_condicionado", bocal), ("9_capuz_saida_ar", capuz_saida)]


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
