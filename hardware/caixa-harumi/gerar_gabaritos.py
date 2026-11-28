#!/usr/bin/env python3
"""Gabaritos em tamanho real (1:1) para testar o encaixe no carro antes de imprimir em 3D.

Gera GABARITOS-1x1.pdf (A4) com:
  1. contorno da moldura da tela de 13,3" (323 x 201, em 2 folhas) com a janela, o centro e a lingueta da articulacao;
  2. base do suporte do painel (180 x 100) com os 4 furos e o rasgo dos cabos: serve de molde para furar;
  3. pegada da caixa da central (205 x 195, 233 com as orelhas) com os furos das orelhas.
Imprimir em "tamanho real" / 100 % (sem "ajustar a pagina") e conferir a regua de 100 mm com uma trena.
Uso: python gerar_gabaritos.py   (precisa de pymupdf)
"""
import os
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_caixa as gc  # noqa: E402
import gerar_caixa_central as cc  # noqa: E402

MM = 72 / 25.4
A4 = (297 * MM, 210 * MM)          # paisagem


def regua(page, x, y):
    """Regua de 100 mm para conferir a escala da impressao."""
    page.draw_line((x * MM, y * MM), ((x + 100) * MM, y * MM), width=1)
    for i in range(11):
        h = 3 if i % 5 else 5
        page.draw_line(((x + i * 10) * MM, y * MM), ((x + i * 10) * MM, (y - h) * MM), width=.6)
    page.insert_text(((x + 102) * MM, (y + 1) * MM), "100 mm: confira com a trena", fontsize=8)


def rect(page, cx, cy, w, h, dash=None, width=1.0):
    r = pymupdf.Rect((cx - w / 2) * MM, (cy - h / 2) * MM, (cx + w / 2) * MM, (cy + h / 2) * MM)
    page.draw_rect(r, width=width, dashes=dash)


def furo(page, cx, cy, d):
    page.draw_circle((cx * MM, cy * MM), d / 2 * MM, width=.8)
    page.draw_line(((cx - d) * MM, cy * MM), ((cx + d) * MM, cy * MM), width=.3)
    page.draw_line((cx * MM, (cy - d) * MM), (cx * MM, (cy + d) * MM), width=.3)


def titulo(page, t, sub):
    page.insert_text((12 * MM, 12 * MM), t, fontsize=13)
    page.insert_text((12 * MM, 17 * MM), sub, fontsize=8)


def main():
    doc = pymupdf.open()
    # 1. moldura da tela (323 mm nao cabe no A4: uma metade por folha; junte pela linha do meio)
    tl, ta, ml, ma, cantos = gc._m10()
    for lado, sinal in (("ESQUERDA", -1), ("DIREITA", 1)):
        p = doc.new_page(width=A4[1], height=A4[0])            # folha em pe
        titulo(p, f'Tela de 13,3" na moldura (vista de frente) - 1:1 - metade {lado}',
               f"Moldura {2 * ml:.0f} x {2 * ma:.0f} mm em 2 folhas: recorte cada metade na linha do meio, junte as duas com fita "
               f"num papelao. Janela {gc.J10_L:.0f} x {gc.J10_A:.0f} tracejada.")
        cy = 150
        cx = 195 if sinal < 0 else 15                         # a linha do meio (x=0) fica perto da borda da folha
        p.draw_rect(pymupdf.Rect(*(v * MM for v in (min(cx, cx + sinal * ml), cy - ma, max(cx, cx + sinal * ml), cy + ma))), width=1.4)
        p.draw_rect(pymupdf.Rect(*(v * MM for v in (min(cx, cx + sinal * gc.J10_L / 2), cy - gc.J10_A / 2,
                                                   max(cx, cx + sinal * gc.J10_L / 2), cy + gc.J10_A / 2))), width=1, dashes="[4 3] 0")
        p.draw_line((cx * MM, (cy - ma - 6) * MM), (cx * MM, (cy + ma + 6) * MM), width=.8, dashes="[6 2 1 2] 0")
        p.insert_text(((cx + 2 if sinal > 0 else cx - 12) * MM, (cy - ma - 8) * MM), "meio", fontsize=8)
        y_eixo = cy + ma - (gc.LING_Y0 + gc.LING_Y1) / 2
        p.draw_line(((cx) * MM, y_eixo * MM), ((cx + sinal * 25) * MM, y_eixo * MM), width=.6)
        if sinal > 0:
            p.insert_text(((cx + 27) * MM, (y_eixo + 1) * MM), f"eixo M6 (a {gc.SUP_ALT:.0f} mm do tampo)", fontsize=7)
        regua(p, 30, 285)
    # 2. base do suporte
    p = doc.new_page(width=A4[0], height=A4[1])
    titulo(p, "Base do suporte no tampo do painel - molde de furacao 1:1",
           "Base 180 x 100 mm. Furos de 4,5 mm (parafuso auto-atarraxante 4,2). Rasgo dos cabos atras (lado do para-brisa).")
    cx, cy = 148.5, 100
    rect(p, cx, cy, 180, 100, width=1.4)
    for x in (-75, 75):
        for z in (12, 88):
            furo(p, cx + x, cy - 50 + (100 - z), 4.5)
    rect(p, cx, cy - 50 + (100 - 82), 30, 16, dash="[3 2] 0")
    p.insert_text(((cx - 14) * MM, (cy - 50 + 8) * MM), "rasgo dos cabos", fontsize=7)
    for s_ in (-1, 1):
        rect(p, cx + s_ * (gc.LING_L / 2 + 0.6 + 3), cy, 6, 30, dash="[2 2] 0")
    p.insert_text(((cx - 10) * MM, (cy + 57) * MM), "v  motorista  v", fontsize=9)
    regua(p, 12, 205)
    # 3. caixa da central (A4 em pe: o comprimento da caixa fica na vertical da folha)
    p = doc.new_page(width=A4[1], height=A4[0])
    titulo(p, "Caixa da central - pegada 1:1 (vista de cima)",
           f"Caixa {cc.EXT_L:.0f} x {cc.EXT_P:.0f} mm, altura {cc.EXT_A:.0f}; com as orelhas {cc.EXT_L + 28:.0f} mm. Furos M4.")
    ox, oy = (210 - cc.EXT_P) / 2, 22 + 14             # x da folha = largura da caixa; y = comprimento
    rect(p, ox + cc.EXT_P / 2, oy + cc.EXT_L / 2, cc.EXT_P, cc.EXT_L, width=1.4)
    for y0 in (-12, cc.EXT_L):
        for zc in (35, cc.EXT_P - 35):
            rect(p, ox + zc, oy + y0 + 6, 24, 12, dash="[2 2] 0")
            furo(p, ox + zc, oy + y0 + 6, 4.4)
    p.insert_text(((ox + 3) * MM, (oy + cc.EXT_L / 2) * MM), "frente", fontsize=7)
    p.insert_text(((ox + cc.EXT_P - 14) * MM, (oy + cc.EXT_L / 2) * MM), "tras", fontsize=7)
    regua(p, 12, 290)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GABARITOS-1x1.pdf")
    doc.save(out)
    print("ok", out, doc.page_count, "paginas")


if __name__ == "__main__":
    main()
