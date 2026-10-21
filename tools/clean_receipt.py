"""Turn the supplied order-receipt art into an empty, reusable frame.

    python -I tools/clean_receipt.py

Reads  assets/source/official/order_receipt.png
Writes assets/draft2/receipt_frame.png and assets/draft2/receipt_frame.webp

Everything that is specific to one order (avatar, name plank, 2/7 badge, detail rows,
the "#01" on the plaque) is painted out with a smooth blend of the surrounding
parchment / plaque, plus a little grain so the fill matches the paper texture.
The game draws the live content back on top.
"""

import os

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "source", "official", "order_receipt.png")
OUT = os.path.join(ROOT, "assets", "draft2", "receipt_frame")


def fill(im, region, known):
    """Replace region pixels that are not known with a normalized blur of the known ones."""
    k = (region & known).astype(np.float32)
    est = np.zeros_like(im)
    have = np.zeros(k.shape, bool)
    for s in (6, 16, 40, 100, 220):                      # finest scale with support wins
        w = ndimage.gaussian_filter(k, s)
        ok = (w > 0.03) & ~have
        for c in range(3):
            est[..., c] = np.where(ok, ndimage.gaussian_filter(im[..., c] * k, s) / np.maximum(w, 1e-6), est[..., c])
        have |= ok
    # anything still too far from clean paper takes the average paper colour
    for c in range(3):
        mean = float((im[..., c] * k).sum() / max(k.sum(), 1))
        est[..., c] = np.where(have, est[..., c], mean)
    # smooth the estimate so the scales blend without seams
    for c in range(3):
        est[..., c] = ndimage.gaussian_filter(est[..., c], 12)
    grain = ndimage.gaussian_filter(np.random.default_rng(3).normal(0, 2.4, k.shape).astype(np.float32), .8)
    target = region & ~known
    out = im.copy()
    for c in range(3):
        out[..., c] = np.where(target, est[..., c] + grain, out[..., c])
    return out


def main():
    im = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
    H, W, _ = im.shape
    yy, xx = np.mgrid[0:H, 0:W]

    # 1. parchment interior (keep the frame's vines in the bottom corners)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    cream = (R > 220) & (G > 200) & (B > 150) & (np.abs(R - G) < 45)
    region = (xx >= 205) & (xx <= 885) & (yy >= 258) & (yy <= 1308) & ~((G > R) & (yy > 1150))
    # the whole content block is replaced; only the clean paper margin around it is sampled
    block = (xx >= 224) & (xx <= 866) & (yy >= 262) & (yy <= 1296)
    content = ndimage.binary_dilation(region & ~cream, iterations=4) | block
    im = fill(im, region, region & ~content)

    # 2. the plaque: clear the number, keep the screws at either end
    R, G = im[..., 0], im[..., 1]
    plaque = (xx >= 448) & (xx <= 640) & (yy >= 188) & (yy <= 246)
    dark = ndimage.binary_dilation(plaque & ~((R > 200) & (G > 170)), iterations=3)
    im = fill(im, plaque, plaque & ~dark)

    out = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8))
    out.save(OUT + ".png")
    web = out.copy()
    web.thumbnail((760, 1020), Image.LANCZOS)
    web.save(OUT + ".webp", "WEBP", quality=86, method=6)
    print("frame", out.size, "| web", web.size, os.path.getsize(OUT + ".webp") // 1024, "KB")


if __name__ == "__main__":
    main()
