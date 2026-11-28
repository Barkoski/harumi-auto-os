#!/usr/bin/env python3
"""Gera os STLs da caixa da Harumi (moldura da tela 7" + caixa 2-DIN para Orange Pi 5, hub, 4G, conversor e fan 40 mm).

Sem bibliotecas 3D: cada peca e montada num grid de voxels (numpy) e a superficie e exportada como STL binario,
juntando faces vizinhas em retangulos para o arquivo ficar pequeno. Os circulos saem em degraus de RES mm.

Uso:  python gerar_caixa.py            -> grava os .stl nesta pasta
TODAS as medidas marcadas [VERIFICAR] sao estimativas: confira com a tela em maos e o vao do radio antes de imprimir.
Eixos: x = largura, y = altura (no carro), z = profundidade (0 = frente, cresce para dentro do painel). Unidade: mm.
"""
from __future__ import annotations

import os
import struct
import sys

import numpy as np

RES = 0.4  # mm por voxel (impressora FDM com bico 0,4: suficiente)

# ---------------- Medidas (ajuste aqui) ----------------
# Tela 7" HDMI 1024x600 (placa + vidro)                      [VERIFICAR com paquimetro]
TELA_L, TELA_A, TELA_E = 166.0, 101.5, 7.0   # largura, altura, espessura do modulo
JANELA_L, JANELA_A = 155.0, 87.0             # area visivel; centralizada [VERIFICAR deslocamento]
FOLGA = 0.6
# Moldura frontal
MOLD_L, MOLD_A = 192.0, 114.0
LABIO = 2.5                                   # espessura da frente sobre a tela
MOLD_P = LABIO + TELA_E + 1.0                 # profundidade total da moldura
# Corpo que entra no vao 2-DIN (180 x 100 pela ISO 7736)    [VERIFICAR o vao do Impreza]
CORPO_L, CORPO_A = 178.0, 98.0
PAREDE = 2.5
FLANGE = 3.0
CORPO_P = 100.0                               # profundidade atras da flange; 100 deixa 19 mm para plugues em 90 graus atras do Pi [VERIFICAR o vao]
# Furos da moldura <-> flange (parafuso M3 auto-atarraxante)
FUROS_MF = [(-89.0, -40.0), (89.0, -40.0), (-89.0, 40.0), (89.0, 40.0)]
# Fan 40 x 40 x 10 sob o Orange Pi
FAN_X, FAN_Z, FAN_FURO = -20.0, 45.0, 32.0    # centro e distancia entre furos (padrao 40 mm: 32)
# Alturas das bandejas (y da face de baixo da bandeja)
Y_BANDEJA_PI = -(CORPO_A / 2 - PAREDE) + 14.0  # deixa 14 mm para a fan
Y_BANDEJA_HUB = 6.0
BANDEJA_E = 2.0

INT_X = CORPO_L / 2 - PAREDE   # meia largura interna
INT_Y = CORPO_A / 2 - PAREDE   # meia altura interna


class Grid:
    def __init__(self, x0, x1, y0, y1, z0, z1):
        self.o = np.array([x0, y0, z0], float)
        self.n = np.ceil((np.array([x1, y1, z1]) - self.o) / RES).astype(int)
        self.v = np.zeros(self.n, bool)

    def _idx(self, a0, a1, ax):
        i0 = int(np.floor((a0 - self.o[ax]) / RES + 1e-6))
        i1 = int(np.ceil((a1 - self.o[ax]) / RES - 1e-6))
        return max(i0, 0), min(i1, self.n[ax])

    def box(self, x0, x1, y0, y1, z0, z1, val=True):
        xi, yi, zi = self._idx(x0, x1, 0), self._idx(y0, y1, 1), self._idx(z0, z1, 2)
        self.v[xi[0]:xi[1], yi[0]:yi[1], zi[0]:zi[1]] = val

    def cyl(self, axis, c1, c2, r, a0, a1, val=True):
        """Cilindro ao longo de 'axis' (0=x,1=y,2=z); c1,c2 = centro nos outros dois eixos (em ordem crescente de eixo)."""
        others = [a for a in range(3) if a != axis]
        lo = self._idx(a0, a1, axis)
        g1 = self.o[others[0]] + (np.arange(self.n[others[0]]) + .5) * RES
        g2 = self.o[others[1]] + (np.arange(self.n[others[1]]) + .5) * RES
        disk = (g1[:, None] - c1) ** 2 + (g2[None, :] - c2) ** 2 <= r * r
        sl = [slice(None)] * 3
        sl[axis] = slice(lo[0], lo[1])
        view = self.v[tuple(sl)]
        d = np.expand_dims(disk, axis)
        if val:
            view |= d
        else:
            view &= ~d

    def mesh(self):
        """Superficie do volume como lista de triangulos (faces coplanares juntas em retangulos)."""
        v = np.pad(self.v, 1)
        tris = []
        for ax in range(3):
            b, c = (ax + 1) % 3, (ax + 2) % 3          # ordem ciclica: normal = +ax
            vv = np.moveaxis(v, (ax, b, c), (0, 1, 2))
            pos = vv[:-1] & ~vv[1:]                      # cheio -> vazio: face com normal +ax no plano i+1
            neg = ~vv[:-1] & vv[1:]                      # vazio -> cheio: normal -ax
            for mask_all, sgn in ((pos, 1), (neg, -1)):
                planes = np.nonzero(mask_all.any(axis=(1, 2)))[0]
                for i in planes:
                    for (r0, r1, s0, s1) in _rects(mask_all[i]):
                        a = self.o[ax] + (i + 1 - 1) * RES        # pad de 1 voxel: plano i+1 -> indice i
                        bb0 = self.o[b] + (r0 - 1) * RES
                        bb1 = self.o[b] + (r1 - 1) * RES
                        cc0 = self.o[c] + (s0 - 1) * RES
                        cc1 = self.o[c] + (s1 - 1) * RES
                        q = []
                        for (pb, pc) in ((bb0, cc0), (bb1, cc0), (bb1, cc1), (bb0, cc1)):
                            p = [0.0, 0.0, 0.0]
                            p[ax], p[b], p[c] = a, pb, pc
                            q.append(p)
                        if sgn > 0:
                            tris.append((q[0], q[1], q[2])); tris.append((q[0], q[2], q[3]))
                        else:
                            tris.append((q[0], q[2], q[1])); tris.append((q[0], q[3], q[2]))
        return tris


def _rects(m):
    """Junta as celulas verdadeiras de uma mascara 2D em retangulos [r0,r1) x [s0,s1) (runs por linha + extensao)."""
    out, active = [], {}
    rows = m.shape[0]
    for r in range(rows + 1):
        runs = set()
        if r < rows:
            row = m[r]
            if row.any():
                d = np.diff(np.concatenate(([0], row.view(np.int8), [0])))
                st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
                runs = set(zip(st.tolist(), en.tolist()))
        nxt = {}
        for k, r0 in active.items():
            if k in runs:
                nxt[k] = r0
            else:
                out.append((r0, r, k[0], k[1]))
        for k in runs:
            if k not in nxt:
                nxt[k] = r
        active = nxt
    return out


def write_stl(path, tris, name):
    arr = np.asarray(tris, np.float32).reshape(-1, 3, 3)
    nrm = np.cross(arr[:, 1] - arr[:, 0], arr[:, 2] - arr[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 0)
    with open(path, "wb") as f:
        f.write(name.encode("ascii", "replace")[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(arr)))
        rec = np.zeros(len(arr), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec["n"], rec["v"] = nrm, arr
        f.write(rec.tobytes())
    vol = float(np.sum(np.einsum("ij,ij->i", arr[:, 0], np.cross(arr[:, 1], arr[:, 2]))) / 6.0)
    return len(arr), vol


# ---------------- Pecas ----------------
def moldura():
    g = Grid(-MOLD_L / 2, MOLD_L / 2, -MOLD_A / 2, MOLD_A / 2, -MOLD_P, 0)
    g.box(-MOLD_L / 2, MOLD_L / 2, -MOLD_A / 2, MOLD_A / 2, -MOLD_P, 0)
    tl, ta = TELA_L / 2 + FOLGA / 2, TELA_A / 2 + FOLGA / 2
    g.box(-tl, tl, -ta, ta, -MOLD_P + LABIO, 0.01, False)                 # bolso da tela (aberto atras)
    g.box(-JANELA_L / 2, JANELA_L / 2, -JANELA_A / 2, JANELA_A / 2, -MOLD_P - 1, 0.01, False)  # janela
    for (x, y) in FUROS_MF:                                               # furo cego M3 (auto-atarraxante)
        g.cyl(2, x, y, 1.3, -8.0, 0.01, False)
    return g


# ---------------- Tela grande: 13,3" Full HD 1920x1080 touch (escolhida em 20/11/2026) ----------------
# (Os nomes T10_/M10_ ficaram da tela de 10,1"; os valores agora sao da 13,3".)
# Medidas ESTIMADAS pelo padrao 16:9 de 13,3" (area ativa ~294 x 165): o anuncio nao foi aberto.   [VERIFICAR com a tela]
# Se a tela vier dentro de uma capa/caixa propria, meca a capa e ponha as medidas dela aqui (a moldura vira um berco).
T10_L, T10_A, T10_E = 306.0, 184.0, 8.0      # modulo (vidro + painel): largura, altura, espessura
J10_L, J10_A = 294.0, 166.0                  # janela visivel
P10_L, P10_A = 140.0, 90.0                   # abertura de tras para a placa controladora e os cabos
CORTE_FRENTE, CORTE_TRAS = -50.0, 50.0       # moldura de 323 mm: cada peca em 2 partes (cortes desencontrados), todas cabem em mesa de 220 x 220
M10_BORDA, M10_TRAS = 8.0, 3.0               # borda da moldura e espessura da parede de tras
M10_DY = 0.0                                 # sobe (+) ou desce (-) a tela em relacao ao vao 2-DIN  [VERIFICAR no painel]


def _m10():
    tl, ta = T10_L / 2 + FOLGA / 2, T10_A / 2 + FOLGA / 2
    ml, ma = tl + M10_BORDA, ta + M10_BORDA
    cantos = [(sx * (ml - M10_BORDA / 2), sy * (ma - M10_BORDA / 2) + M10_DY) for sx in (-1, 1) for sy in (-1, 1)]
    cantos += [(x, sy * (ma - M10_BORDA / 2) + M10_DY) for x in (CORTE_FRENTE - 12, CORTE_FRENTE + 12,
                                                                   CORTE_TRAS - 12, CORTE_TRAS + 12) for sy in (-1, 1)]
    return tl, ta, ml, ma, cantos


def moldura10():
    """Frente da moldura flutuante da tela de 10,1": aba com a janela e bolso aberto atras (a tela entra por tras).
    Fica na frente do vao 2-DIN, mais larga e mais alta que ele. 4 furos cegos M3 nos cantos para a traseira."""
    tl, ta, ml, ma, cantos = _m10()
    prof = LABIO + T10_E + 0.5
    g = Grid(-ml, ml, -ma + M10_DY, ma + M10_DY, -prof - M10_TRAS, -M10_TRAS)
    g.box(-ml, ml, -ma + M10_DY, ma + M10_DY, -prof - M10_TRAS, -M10_TRAS)
    g.box(-tl, tl, -ta + M10_DY, ta + M10_DY, -prof - M10_TRAS + LABIO, -M10_TRAS + 1, False)       # bolso
    g.box(-J10_L / 2, J10_L / 2, -J10_A / 2 + M10_DY, J10_A / 2 + M10_DY, -prof - M10_TRAS - 1,
          -prof - M10_TRAS + LABIO + 0.01, False)                                                  # janela
    for (x, y) in cantos:
        g.cyl(2, x, y, 1.3, -M10_TRAS - 7, -M10_TRAS + 1, False)
    return g


# Articulacao: lingueta atras da traseira + suporte no tampo do painel, eixo M6 com porca autotravante (inclinacao por atrito)
LING_L, LING_Y0, LING_Y1, LING_P = 40.0, 15.0, 45.0, 20.0   # largura, faixa de altura a partir da borda de baixo, profundidade
EIXO_R = 3.2                                                 # furo do parafuso M6
SUP_ALT = 40.0                                               # altura do eixo sobre o tampo do painel  [VERIFICAR visao]


def traseira10():
    """Traseira da moldura de 10,1": prende a tela no bolso (4 x M3 nos cantos), abertura central para a placa da tela
    e os cabos, grade de ar e a lingueta da articulacao (furo M6) que encaixa no suporte do painel."""
    tl, ta, ml, ma, cantos = _m10()
    g = Grid(-ml, ml, -ma + M10_DY, ma + M10_DY, -M10_TRAS, LING_P)
    g.box(-ml, ml, -ma + M10_DY, ma + M10_DY, -M10_TRAS, 0)
    g.box(-P10_L / 2, P10_L / 2, -P10_A / 2 + M10_DY, P10_A / 2 + M10_DY, -M10_TRAS - 1, 1, False)
    for (x, y) in cantos:
        g.cyl(2, x, y, 1.7, -M10_TRAS - 1, 1, False)
    for i in range(6):                                                       # grade de ar atras do painel
        x = -140 + i * 8
        g.box(x, x + 4, -32 + M10_DY, 32 + M10_DY, -M10_TRAS - 1, 1, False)
        g.box(-x - 4, -x, -32 + M10_DY, 32 + M10_DY, -M10_TRAS - 1, 1, False)
    y0, y1 = -ma + LING_Y0 + M10_DY, -ma + LING_Y1 + M10_DY
    g.box(-LING_L / 2 - 10, LING_L / 2 + 10, y0 - 5, y1 + 3, 0, 5)          # pe que espalha o esforco
    g.box(-LING_L / 2, LING_L / 2, y0, y1, 0, LING_P)                        # lingueta
    g.cyl(0, (y0 + y1) / 2, LING_P - 8, EIXO_R, -LING_L / 2 - 1, LING_L / 2 + 1, False)
    return g


def suporte_painel():
    """Suporte da tela no tampo do painel: base de 180 x 100 com 4 furos (parafuso auto-atarraxante 4,2 ou fita VHB +
    parafuso), duas orelhas com o eixo M6 e reforcos. Rasgo atras para os cabos HDMI e USB descerem para o painel."""
    folga = 0.6
    xi = LING_L / 2 + folga                       # face interna das orelhas
    g = Grid(-90, 90, 0, SUP_ALT + 10, 0, 100)
    g.box(-90, 90, 0, 5, 0, 100)                                             # base
    for s in (-1, 1):
        x0, x1 = sorted((s * xi, s * (xi + 6)))
        g.box(x0, x1, 0, SUP_ALT + 10, 35, 65)                               # orelha
        for i in range(8):                                                   # reforco em degraus
            h = SUP_ALT - i * 5
            a0, a1 = sorted((s * (xi + 6 + i * 3), s * (xi + 9 + i * 3)))
            g.box(a0, a1, 5, 5 + h, 45, 55)
    g.cyl(0, SUP_ALT, 50, EIXO_R, -95, 95, False)                            # eixo M6
    for x in (-75, 75):
        for z in (12, 88):
            g.cyl(1, x, z, 2.25, -1, 6, False)                               # furos de fixacao
    g.box(-15, 15, -1, 6, 74, 90, False)                                     # rasgo dos cabos
    return g


def caixa():
    z_fim = FLANGE + CORPO_P
    g = Grid(-MOLD_L / 2, MOLD_L / 2, -MOLD_A / 2, MOLD_A / 2, 0, z_fim)
    g.box(-MOLD_L / 2, MOLD_L / 2, -MOLD_A / 2, MOLD_A / 2, 0, FLANGE)                     # flange
    g.box(-CORPO_L / 2, CORPO_L / 2, -CORPO_A / 2, CORPO_A / 2, FLANGE, z_fim)             # corpo
    g.box(-INT_X, INT_X, -INT_Y, INT_Y, FLANGE, z_fim + 1, False)                          # oco (fundo aberto)
    g.box(-75, 75, -40, 40, -1, FLANGE + 0.01, False)                                      # passagem dos cabos da tela
    for (x, y) in FUROS_MF:
        g.cyl(2, x, y, 1.7, -1, FLANGE + 1, False)
    # trilhos das bandejas (2 alturas), um em cada parede lateral
    for yb in (Y_BANDEJA_PI,):                       # so a bandeja do Pi (hub e 4G foram para a caixinha de servico)
        for s in (-1, 1):
            x0, x1 = sorted((s * INT_X, s * (INT_X - 3.0)))
            g.box(x0, x1, yb - 2.0, yb, FLANGE + 6, z_fim - 10)
    # fan 40 mm no fundo: abertura com grade (anel + cruz) e 4 furos M3
    fz = FLANGE + FAN_Z
    g.cyl(1, FAN_X, fz, 19.0, -CORPO_A / 2 - 1, -INT_Y + 0.01, False)
    g.cyl(1, FAN_X, fz, 11.0, -CORPO_A / 2, -INT_Y)
    g.cyl(1, FAN_X, fz, 9.0, -CORPO_A / 2 - 1, -INT_Y + 0.01, False)
    g.box(FAN_X - 1, FAN_X + 1, -CORPO_A / 2, -INT_Y, fz - 19, fz + 19)
    g.box(FAN_X - 19, FAN_X + 19, -CORPO_A / 2, -INT_Y, fz - 1, fz + 1)
    for dx in (-FAN_FURO / 2, FAN_FURO / 2):
        for dz in (-FAN_FURO / 2, FAN_FURO / 2):
            g.cyl(1, FAN_X + dx, fz + dz, 1.7, -CORPO_A / 2 - 1, -INT_Y + 0.01, False)
    # entrada de ar extra no fundo (lado do conversor) e grade de saida no topo
    for i in range(5):
        x = 22 + i * 12
        g.box(x, x + 4, -CORPO_A / 2 - 1, -INT_Y + 0.01, FLANGE + 25, FLANGE + 65, False)
    for i in range(13):
        x = -66 + i * 11
        g.box(x, x + 4, INT_Y - 0.01, CORPO_A / 2 + 1, FLANGE + 20, FLANGE + 70, False)
    # furos laterais para suporte/gaiola do radio (M3)                                    [VERIFICAR]
    for s in (-1, 1):
        for zz in (FLANGE + 30, FLANGE + 60):
            g.cyl(0, 0.0, zz, 1.7, s * CORPO_L / 2 - 4 if s > 0 else -CORPO_L / 2 - 1,
                  CORPO_L / 2 + 1 if s > 0 else -INT_X + 0.01, False)
    # colunas dos 4 parafusos da tampa (furo 2,6 mm para M3 auto-atarraxante)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (INT_X - 3.5), sy * (INT_Y - 3.5)
            g.box(cx - 3.5, cx + 3.5, cy - 3.5, cy + 3.5, z_fim - 16, z_fim)
            g.cyl(2, cx, cy, 1.3, z_fim - 12, z_fim + 1, False)
    return g


def bandeja(tipo):
    lx = INT_X - 0.4          # folga para deslizar nos trilhos
    p0, p1 = FLANGE + 6, FLANGE + CORPO_P - 17      # termina antes das colunas da tampa
    g = Grid(-lx, lx, 0, BANDEJA_E, p0, p1)
    g.box(-lx, lx, 0, BANDEJA_E, p0, p1)
    zc = FLANGE + FAN_Z
    if tipo == "pi":
        g.box(FAN_X - 22, FAN_X + 22, -1, 3, zc - 22, zc + 22, False)       # janela de ar sobre a fan
        for dx in (-46, 46):                                                 # janelas para os parafusos M2.5
            for dz in (-27, 27):                                             # do Pi (posicao livre)  [VERIFICAR]
                g.box(FAN_X + dx - 6, FAN_X + dx + 6, -1, 3, zc + dz - 6, zc + dz + 6, False)
        for i in range(6):                                                   # furos de ar sob o conversor
            g.cyl(1, 30 + (i % 3) * 16, zc - 12 + (i // 3) * 24, 4.0, -1, 3, False)
    else:
        for i in range(8):                                                   # grade de ar
            g.box(-70 + i * 18, -62 + i * 18, -1, 3, zc - 30, zc + 30, False)
        for x in (-80, -30, 20, 70):                                         # pares de fendas para abracadeira
            for zz in (p0 + 6, p1 - 9):
                g.box(x, x + 4, -1, 3, zz, zz + 3, False)
    return g


def tampa():
    t = 2.5
    g = Grid(-CORPO_L / 2, CORPO_L / 2, -CORPO_A / 2, CORPO_A / 2, 0, t)
    g.box(-CORPO_L / 2, CORPO_L / 2, -CORPO_A / 2, CORPO_A / 2, 0, t)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.cyl(2, sx * (INT_X - 3.5), sy * (INT_Y - 3.5), 1.7, -1, t + 1, False)
    for i in range(7):                                                       # grade de saida de ar
        y = 6 + i * 5.5
        g.box(-70, 10, y, y + 3, -1, t + 1, False)
    for (x, y) in ((40, 25), (65, 25), (40, -10), (65, -10)):                # passa-fios 14 mm
        g.cyl(2, x, y, 7.0, -1, t + 1, False)
    g.box(-70, -20, -32, -22, -1, t + 1, False)                              # rasgo para o cabo de 12 V/ACC
    for x in (-62, -22):                                                     # fendas de abracadeira: conversor 12->5 V
        for y in (-20, 2):                                                   # preso por fora da tampa (66 x 60 mm)
            g.box(x, x + 4, y, y + 3, -1, t + 1, False)
    return g


# Plano novo (20/11/2026): tela de 10,1" em cima do painel; a caixa 2-DIN saiu (o vao do carro e 1-DIN e o radio fica).
PECAS = [("1b_moldura_tela_13pol", moldura10, CORTE_FRENTE), ("1c_traseira_tela_13pol", traseira10, CORTE_TRAS),
         ("1d_suporte_tela_painel", suporte_painel, None)]
# Pecas do plano 2-DIN antigo (arquivadas em antigo-2din/); para gerar de novo, rode com PECAS = PECAS_2DIN.
PECAS_2DIN = [("1_moldura_tela", moldura, None), ("2_caixa_2din", caixa, None),
              ("3_bandeja_pi", lambda: bandeja("pi"), None), ("5_tampa_traseira", tampa, None)]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    saida = []
    for name, fn, corte in PECAS:
        g = fn()
        if corte is None:
            saida.append((name, g))
            continue
        i = int(round((corte - g.o[0]) / RES))                 # corta em x: parte esquerda e parte direita
        esq, dir_ = Grid.__new__(Grid), Grid.__new__(Grid)
        for parte in (esq, dir_):
            parte.o, parte.n, parte.v = g.o.copy(), g.n.copy(), g.v.copy()
        esq.v[i:] = False
        dir_.v[:i] = False
        saida += [(name + "_esq", esq), (name + "_dir", dir_)]
    for name, g in saida:
        tris = g.mesh()
        n, vol = write_stl(os.path.join(here, name + ".stl"), tris, "Harumi " + name)
        vox = float(g.v.sum()) * RES ** 3
        ok = abs(vol - vox) / vox < 1e-3
        occ = [np.nonzero(g.v.any(axis=tuple(k for k in range(3) if k != ax)))[0] for ax in range(3)]
        dims = np.array([(o[-1] - o[0] + 1) * RES for o in occ])          # tamanho real da peca
        print(f"{name}: {n} triangulos, {dims[0]:.0f} x {dims[1]:.0f} x {dims[2]:.0f} mm, "
              f"volume {vol / 1000:.1f} cm3 (voxels {vox / 1000:.1f}) {'OK' if ok else 'ERRO'}", flush=True)
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
