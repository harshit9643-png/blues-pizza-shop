"""Cut the supplied coconut tray out of its table-and-leaves background.

    python -I tools/cut_tray.py

Reads  assets/source/official/coconut_tray.png
Writes assets/draft2/coconut_tray_cut.png (full size) and assets/draft2/coconut_tray.webp (game size)

Steps:
  1. follow the tray's dark outer outline in 720 directions from its centre
     (plank seams give isolated long readings, replaced by the local median)
  2. clear light plank pixels that are connected to the outside
  3. shave slivers thinner than ~9 px
  4. along the bottom edge, clear everything below the near-black outer outline
     (the tray sits on a strip of shadowed plank there that has its own outline)
"""

import math
import os
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "source", "official", "coconut_tray.png")
OUT_PNG = os.path.join(ROOT, "assets", "draft2", "coconut_tray_cut.png")
OUT_WEB = os.path.join(ROOT, "assets", "draft2", "coconut_tray.webp")
CX, CY = 678, 572           # tray centre in the source image


def main():
    src = Image.open(SRC).convert("RGB")
    im = np.asarray(src).astype(int)
    H, W, _ = im.shape
    R, G = im[..., 0], im[..., 1]

    # 1. outline-following polygon
    N = 720
    rs = np.zeros(N)
    for i in range(N):
        t = 2 * math.pi * i / N
        dx, dy = math.cos(t), math.sin(t)
        r, hit = 705, 560
        while r > 300:
            x, y = int(round(CX + dx * r)), int(round(CY + dy * r))
            if 0 <= x < W and 0 <= y < H and R[y, x] < 170 and G[y, x] < 100:
                hit = r
                break
            r -= 1
        rs[i] = hit
    med = np.array([np.median(np.take(rs, range(i - 12, i + 13), mode="wrap")) for i in range(N)])
    clean = np.where(rs > med + 14, med, rs)
    clean = np.array([np.median(np.take(clean, range(i - 2, i + 3), mode="wrap")) for i in range(N)])
    S = 4
    m = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(m).polygon(
        [((CX + math.cos(2 * math.pi * i / N) * (clean[i] + 1.5)) * S,
          (CY + math.sin(2 * math.pi * i / N) * (clean[i] + 1.5)) * S) for i in range(N)], fill=255)
    alpha = np.asarray(m.resize((W, H), Image.LANCZOS)).astype(np.uint8).copy()

    # 2. plank pixels connected to the outside
    plank = (G >= 132) & (R >= 212)
    seen = alpha < 128
    q = deque(zip(*np.where(seen)))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and plank[ny, nx]:
                seen[ny, nx] = True
                alpha[ny, nx] = 0
                q.append((ny, nx))

    # 3. thin slivers
    a = Image.fromarray(alpha)
    hard = a.point(lambda v: 255 if v > 127 else 0).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9))
    alpha = np.minimum(alpha, np.asarray(hard.filter(ImageFilter.GaussianBlur(.8))))

    # 4. bottom edge: nothing below the near-black outer outline
    outline = (R < 92) & (G < 36) & (alpha > 150)
    y0 = int(H * .80)
    for x in range(W):
        ys = np.where(outline[y0:, x])[0]
        if len(ys):
            alpha[y0 + ys.max() + 2:, x] = 0

    rgba = src.convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha))
    bb = rgba.getchannel("A").getbbox()
    cut = rgba.crop((bb[0] - 3, bb[1] - 3, bb[2] + 3, bb[3] + 3))
    cut.save(OUT_PNG)
    web = cut.copy()
    web.thumbnail((900, 900), Image.LANCZOS)
    web.save(OUT_WEB, "WEBP", quality=88, method=6)
    print("cut", cut.size, "offset from source", (bb[0] - 3, bb[1] - 3), "| web", web.size,
          os.path.getsize(OUT_WEB) // 1024, "KB")


if __name__ == "__main__":
    main()
