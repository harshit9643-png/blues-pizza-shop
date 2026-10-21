"""Shrink the generated art to web weight.

Reads assets/characters, assets/props and assets/backgrounds and writes the
WebP files the game loads into assets/web. Characters and props keep their
alpha at 512px; the backdrop stays opaque and wide. Originals are untouched.

    python -I tools/optimize_assets.py
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRCS = [os.path.join(ROOT, "assets", d) for d in ("characters", "props", "game", "backgrounds")]
OUT = os.path.join(ROOT, "assets", "web")

CHAR_MAX = 512
BACKDROP_MAX = 1400


def main():
    os.makedirs(OUT, exist_ok=True)

    total_in = total_out = 0
    rows = []
    files = [(d, fn) for d in SRCS if os.path.isdir(d) for fn in sorted(os.listdir(d))]
    for folder, fn in files:
        stem, ext = os.path.splitext(fn)
        if ext.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        src = os.path.join(folder, fn)
        im = Image.open(src)
        opaque = ext.lower() in (".jpg", ".jpeg")

        if opaque:
            im = im.convert("RGB")
            im.thumbnail((BACKDROP_MAX, BACKDROP_MAX), Image.LANCZOS)
            kw = dict(quality=80, method=6)
        else:
            im = im.convert("RGBA")
            im.thumbnail((CHAR_MAX, CHAR_MAX), Image.LANCZOS)
            kw = dict(quality=86, method=6)

        dest = os.path.join(OUT, stem + ".webp")
        im.save(dest, "WEBP", **kw)

        a, b = os.path.getsize(src), os.path.getsize(dest)
        total_in += a
        total_out += b
        rows.append((stem, im.size, a, b))

    for stem, size, a, b in rows:
        print("{:<14} {:>4}x{:<4}  {:>6.0f} KB -> {:>5.0f} KB".format(
            stem, size[0], size[1], a / 1024, b / 1024))
    print("\n{} files   {:.1f} MB -> {:.1f} MB".format(
        len(rows), total_in / 1048576, total_out / 1048576))


if __name__ == "__main__":
    sys.exit(main() or 0)
