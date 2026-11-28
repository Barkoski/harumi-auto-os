#!/usr/bin/env python3
"""Previa (PNG) das pecas do sistema de sensores 360, desenhada dos proprios .stl (so numpy + zlib)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "caixa-harumi"))
import previa as pv  # noqa: E402

pv.HERE = HERE
pv.PARTES = [("1_caixa_no_sensores", (0, 0, 0), (120, 112, 130)), ("2_tampa_no_sensores", (0, 0, 70), (150, 140, 160)),
             ("3_anel_ultrassom_reto", (95, -30, 0), (90, 160, 120)), ("4_anel_ultrassom_10graus", (130, -30, 0), (90, 160, 120)),
             ("5_suporte_radar_canto_20", (110, 25, 0), (210, 120, 100)), ("6_suporte_lidar_frente", (-110, -15, 0), (150, 130, 200))]
if __name__ == "__main__":
    a = pv.render(np.radians(-30), np.radians(-35))
    b = pv.render(np.radians(150), np.radians(-30))
    pv.save_png(os.path.join(HERE, "previa_pecas.png"), np.concatenate([a, b], axis=1))
    print("ok")
