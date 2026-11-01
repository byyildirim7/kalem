#!/usr/bin/env python3
# Ardışık kareler arası ortalama parlaklık farkının en büyüğü (0-255).
import sys, subprocess, numpy as np
v = sys.argv[1]
raw = subprocess.run(["ffmpeg","-v","error","-i",v,"-vf","scale=480:270,format=gray","-f","rawvideo","-"],capture_output=True).stdout
a = np.frombuffer(raw, np.uint8).reshape(-1, 270*480).astype(np.float64).mean(1)
d = np.abs(np.diff(a)); print(f"kare={len(a)} ort_parlaklik min={a.min():.2f} maks={a.max():.2f} | kareler arasi en buyuk fark={d.max():.3f}/255 (kare {d.argmax()}->{d.argmax()+1})")
