#!/usr/bin/env python3
"""Gera os STLs das pecas impressas do sistema de sensores 360 da Harumi.

Reaproveita o gerador por voxels da caixa da central (../caixa-harumi/gerar_caixa.py): so precisa de Python + numpy.
Uso:  python gerar_pecas.py      -> grava os .stl nesta pasta
TODAS as medidas marcadas [VERIFICAR] sao estimativas: confira com as pecas em maos antes de imprimir.
Unidade: mm. Imprimir em ASA (ou PETG); as pecas do para-choque ficam no sol e na chuva.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "caixa-harumi"))
import gerar_caixa as gc  # noqa: E402  (Grid, write_stl, RES)

# ---------------- Medidas ----------------
# Caixa do no de sensores (ESP32-S3 + placa perfurada + conversor 12->5 V)
CX_L, CX_A, CX_H, CX_P = 110.0, 75.0, 40.0, 2.5    # largura, profundidade, altura, parede
PERF_L, PERF_A = 70.0, 50.0                        # placa perfurada 5x7 cm               [VERIFICAR]
PG_FURO = 12.6                                     # prensa-cabo PG7 (rosca 12,5 mm)       [VERIFICAR]
# Sensor ultrassonico JSN-SR04T (sonda)
SONDA_D = 18.5                                     # diametro do furo da sonda             [VERIFICAR]
ANEL_D = 28.0
# Radar 24 GHz (HLK-LD2451): placa                  [VERIFICAR medidas do modulo]
RADAR_L, RADAR_A = 46.0, 36.0
# Lidar TFmini Plus                                 [VERIFICAR: ~35 x 18,5 x 21 mm de memoria]
LID_L, LID_A, LID_P = 35.5, 19.0, 21.5


class G(gc.Grid):
    def coords(self):
        r = gc.RES
        xs = self.o[0] + (np.arange(self.n[0]) + .5) * r
        ys = self.o[1] + (np.arange(self.n[1]) + .5) * r
        zs = self.o[2] + (np.arange(self.n[2]) + .5) * r
        return np.meshgrid(xs, ys, zs, indexing="ij")

    def where(self, mask, val=True):
        if val:
            self.v |= mask
        else:
            self.v &= ~mask


def caixa_no():
    h, p = CX_H, CX_P
    g = G(-CX_L / 2 - 12, CX_L / 2 + 12, -CX_A / 2, CX_A / 2, 0, h)
    g.box(-CX_L / 2, CX_L / 2, -CX_A / 2, CX_A / 2, 0, h)
    g.box(-CX_L / 2 + p, CX_L / 2 - p, -CX_A / 2 + p, CX_A / 2 - p, p, h + 1, False)
    # degrau para a tampa (encaixe de 1,2 mm) e canal da vedacao
    g.box(-CX_L / 2 + 1.2, CX_L / 2 - 1.2, -CX_A / 2 + 1.2, CX_A / 2 - 1.2, h - 3, h + 1, False)
    # orelhas de fixacao com 2 furos M4 de cada lado
    for s in (-1, 1):
        x0, x1 = sorted((s * CX_L / 2, s * (CX_L / 2 + 12)))
        g.box(x0, x1, -18, 18, 0, 4)
        g.cyl(2, s * (CX_L / 2 + 6), 0, 2.2, -1, 6, False)
    # colunas da tampa (M3 auto-atarraxante) e da placa perfurada
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (CX_L / 2 - p - 3.5), sy * (CX_A / 2 - p - 3.5)
            g.box(cx - 3.5, cx + 3.5, cy - 3.5, cy + 3.5, p, h - 3)
            g.cyl(2, cx, cy, 1.3, h - 15, h, False)
            px, py = sx * (PERF_L / 2 - 2.5), sy * (PERF_A / 2 - 2.5)
            g.cyl(2, px, py, 3.0, p, p + 6)
            g.cyl(2, px, py, 1.15, p, p + 7, False)
    # prensa-cabos: 4 em cada parede comprida (sensores) e 1 em cada lateral (energia e USB)
    for sy in (-1, 1):
        for i in range(4):
            x = -36 + i * 24
            y0, y1 = sorted((sy * (CX_A / 2 + 1), sy * (CX_A / 2 - p - 1)))
            g.cyl(1, x, h / 2 + 2, PG_FURO / 2, y0, y1, False)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (CX_L / 2 + 1), sx * (CX_L / 2 - p - 1)))
        g.cyl(0, 0.0, h / 2 + 2, PG_FURO / 2, x0, x1, False)
    return g


def tampa_no():
    t = 3.0
    g = G(-CX_L / 2, CX_L / 2, -CX_A / 2, CX_A / 2, 0, t + 2.5)
    g.box(-CX_L / 2, CX_L / 2, -CX_A / 2, CX_A / 2, 0, t)
    # aba que entra no degrau da caixa (folga 0,3) com canal para cordao de vedacao de 2 mm
    g.box(-CX_L / 2 + 1.5, CX_L / 2 - 1.5, -CX_A / 2 + 1.5, CX_A / 2 - 1.5, t, t + 2.5)
    g.box(-CX_L / 2 + 3.5, CX_L / 2 - 3.5, -CX_A / 2 + 3.5, CX_A / 2 - 3.5, t, t + 2.6, False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.cyl(2, sx * (CX_L / 2 - CX_P - 3.5), sy * (CX_A / 2 - CX_P - 3.5), 1.7, -1, t + 3, False)
    return g


def anel(inclinacao_graus):
    """Anel que prende a sonda no para-choque. Com inclinacao, a base e uma cunha (sensor apontado para baixo/fora)."""
    r = ANEL_D / 2
    base = 3.0
    ext = base + np.tan(np.radians(inclinacao_graus)) * ANEL_D
    g = G(-r, r, -r, r, 0, ext + 1)
    X, Y, Z = g.coords()
    rr = X ** 2 + Y ** 2
    topo = base + np.tan(np.radians(inclinacao_graus)) * (Y + r)    # cunha ao longo de y
    g.where((rr <= r * r) & (Z <= topo))
    g.where(rr <= (SONDA_D / 2) ** 2, False)
    # 2 abas de travamento (encaixe por tras do para-choque) e 2 furos para parafuso fino
    for s in (-1, 1):
        g.cyl(2, s * (r - 3.2), 0, 1.0, -1, ext + 2, False)
    return g


def suporte_radar(angulo):
    """Placa para o radar com base em cunha (angulo em graus: 0 = atras do para-choque, 45 = canto)."""
    m = 6.0
    L, A = RADAR_L + 2 * m, RADAR_A + 2 * m
    alt = 3.0 + np.tan(np.radians(angulo)) * L
    g = G(-L / 2, L / 2, -A / 2, A / 2, 0, alt + 6)
    X, Y, Z = g.coords()
    topo = 3.0 + np.tan(np.radians(angulo)) * (X + L / 2)
    g.where((np.abs(X) <= L / 2) & (np.abs(Y) <= A / 2) & (Z <= topo))
    # moldura que segura a placa do radar (encaixe por cima, 2 mm de borda)
    borda = (np.abs(X) <= L / 2) & (np.abs(Y) <= A / 2) & (Z > topo) & (Z <= topo + 4)
    dentro = (np.abs(X) <= RADAR_L / 2 + 0.3) & (np.abs(Y) <= RADAR_A / 2 + 0.3)
    g.where(borda & ~dentro)
    g.box(-L / 2 + 4, L / 2 - 4, -A / 2 + 4, A / 2 - 4, -1, 2.0, False)       # alivio de peso na base
    g.box(-4, 4, -A / 2 - 1, -RADAR_A / 2 + 2, 0, alt + 6, False)            # saida do cabo
    return g


def suporte_lidar():
    p = 2.5
    L, A, P = LID_L + 2 * p, LID_A + 2 * p, LID_P + p
    g = G(-L / 2 - 10, L / 2 + 10, 0, A + 0.01, 0, P)
    g.box(-L / 2, L / 2, 0, A, 0, P)
    g.box(-LID_L / 2, LID_L / 2, p, p + LID_A, p, P + 1, False)               # berco (aberto atras)
    g.box(-15, 15, p + 2, p + LID_A - 2, -1, p + 0.01, False)                # janela das lentes
    g.box(-6, 6, A - p - 0.01, A + 1, P - 8, P + 1, False)                    # saida do cabo
    for s in (-1, 1):                                                          # orelhas M4
        x0, x1 = sorted((s * L / 2, s * (L / 2 + 10)))
        g.box(x0, x1, 0, 4, 0, P)
        g.cyl(1, s * (L / 2 + 5), P / 2, 2.2, -1, 5, False)
    return g


PECAS = [
    ("1_caixa_no_sensores", caixa_no, "2 (frente e tras)"),
    ("2_tampa_no_sensores", tampa_no, "2"),
    ("3_anel_ultrassom_reto", lambda: anel(0), "8 (para-choques)"),
    ("4_anel_ultrassom_10graus", lambda: anel(10), "4 (laterais)"),
    ("5_suporte_radar_canto_20", lambda: suporte_radar(20), "4 (cantos; o canto do para-choque ja e curvo)"),
    ("6_suporte_lidar_frente", suporte_lidar, "1"),
]


def main():
    for name, fn, qtd in PECAS:
        g = fn()
        n, vol = gc.write_stl(os.path.join(HERE, name + ".stl"), g.mesh(), "Harumi " + name)
        vox = float(g.v.sum()) * gc.RES ** 3
        ok = abs(vol - vox) / vox < 1e-3
        d = g.n * gc.RES
        print(f"{name}: x{qtd}, {d[0]:.0f} x {d[1]:.0f} x {d[2]:.0f} mm, {vol / 1000:.1f} cm3, {n} tri {'OK' if ok else 'ERRO'}")
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
