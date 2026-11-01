#!/usr/bin/env python3
"""Eskizden yalniz murekkebi ayir: kaynak/ref-01-yan.png -> eskiz-cizgi.png (RGBA).
Kagit rengi koselerden olculur; kagittan koyu her piksel 'renkten alfaya' ile murekkep olur,
kagittan acik (kanat zari dolgusu) seffaf kalir. Boylece eskiz bizim kagidimizin ustune oturur."""
import os
import numpy as np
from PIL import Image

B = os.path.dirname(os.path.abspath(__file__))
im = np.asarray(Image.open(os.path.join(B, 'kaynak', 'ref-01-yan.png')).convert('RGB')).astype(np.float32) / 255.0
h, w, _ = im.shape
k = 40
kose = np.concatenate([im[:k, :k].reshape(-1, 3), im[:k, -k:].reshape(-1, 3), im[-k:, :k].reshape(-1, 3), im[-k:, -k:].reshape(-1, 3)])
bg = np.median(kose, axis=0)
# renkten alfaya: her kanalda kagittan ne kadar koyu
a = np.max((bg - im) / np.maximum(bg, 1e-3), axis=2)
a = np.clip((a - 0.06) / 0.45, 0, 1)          # kagit lekesi/dokusu yok sayilir, cizgi tam doygun
a = a ** 0.85
renk = np.clip(bg - (bg - im) / np.maximum(a[..., None], 1e-3) * 0.55, 0, 1)
renk = np.where(a[..., None] > 1e-3, renk, 0)
# murekkebi defter tonuna cek: kirmizi krank kalsin, gerisi kahverengi murekkep
mur = np.array([0x2b, 0x1d, 0x12], np.float32) / 255
kir = (im[..., 0] - im[..., 1]) > 0.12
renk = np.where(kir[..., None], renk, mur * 0.55 + renk * 0.45)
out = np.dstack([renk, a]) * 255
Image.fromarray(out.astype(np.uint8), 'RGBA').save(os.path.join(B, 'eskiz-cizgi.png'), optimize=True)
print('kagit', (bg * 255).round(), 'boyut', w, h)
