#!/usr/bin/env python3
"""Desenha uma previa (PNG) das pecas a partir dos proprios .stl, sem bibliotecas graficas (so numpy + zlib).
Uso: python previa.py   -> grava previa_caixa.png nesta pasta."""
import os
import struct
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PARTES = [("1_moldura_tela", (0, 0, -70), (150, 140, 160)), ("2_caixa_2din", (0, 0, 0), (120, 112, 130)),
          ("3_bandeja_pi", (0, -32.5, 0), (90, 160, 120)), ("4_bandeja_hub_4g", (0, 6, 0), (150, 130, 200)),
          ("5_tampa_traseira", (0, 0, 160), (120, 112, 130))]


def load(p):
    b = open(p, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    rec = np.frombuffer(b[84:84 + n * 50], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return rec["v"].astype(np.float64), rec["n"].astype(np.float64)


def render(view_yaw, view_pitch, W=900, H=700):
    img = np.full((H, W, 3), 255.0)
    zb = np.full((H, W), np.inf)
    cy, sy, cp, sp = np.cos(view_yaw), np.sin(view_yaw), np.cos(view_pitch), np.sin(view_pitch)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    R = Rx @ Ry
    light = np.array([0.3, 0.7, -0.65]); light /= np.linalg.norm(light)
    allv = []
    for name, off, col in PARTES:
        v, n = load(os.path.join(HERE, name + ".stl"))
        allv.append((v + off, n, np.array(col, float)))
    pts = np.concatenate([a[0].reshape(-1, 3) for a in allv]) @ R.T
    lo, hi = pts.min(0), pts.max(0)
    s = 0.88 * min(W / (hi[0] - lo[0]), H / (hi[1] - lo[1]))
    cx, cyy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    for v, n, col in allv:
        P = v @ R.T
        N = n @ R.T
        shade = 0.35 + 0.65 * np.clip(-(N @ (R @ light)) * -1, 0, 1)
        X = (P[:, :, 0] - cx) * s + W / 2
        Y = H / 2 - (P[:, :, 1] - cyy) * s
        Z = P[:, :, 2]
        for t in range(len(P)):
            x, y, z = X[t], Y[t], Z[t]
            x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W - 1))
            y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H - 1))
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
            d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(d) < 1e-9:
                continue
            a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
            b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
            c = 1 - a - b
            m = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
            if not m.any():
                continue
            zz = a * z[0] + b * z[1] + c * z[2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            w = m & (zz < sub)
            sub[w] = zz[w]
            img[y0:y1 + 1, x0:x1 + 1][w] = col * shade[t]
    return img


def save_png(path, img):
    h, w, _ = img.shape
    raw = b"".join(b"\x00" + np.clip(img[r], 0, 255).astype(np.uint8).tobytes() for r in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    a = render(np.radians(-35), np.radians(-22))
    b = render(np.radians(145), np.radians(-25))
    save_png(os.path.join(HERE, "previa_caixa.png"), np.concatenate([a, b], axis=1))
    print("ok")
