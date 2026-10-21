"""Remove magenta spill left by the chroma key.

The image model likes to paint a soft glow around luminous characters, and that
glow blends with the magenta backing plate, leaving a pink halo. Magenta is the
one hue nothing in this cast actually uses: a pink cast is pixels where red AND
blue both sit above green. Warm fur (red > green > blue) and the pale blue wings
(blue > green > red) both fail that test, so they are left alone.

    python -I tools/despill.py            # whole set
    python -I tools/despill.py noori      # one asset
"""

import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "characters")

CAST = 8       # how far red and blue must exceed green to count as pink
GHOST = 110    # faint pink below this alpha is halo, not character


def despill(path):
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    fixed = cleared = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if r > g + CAST and b > g + CAST:
                if a < GHOST:
                    px[x, y] = (0, 0, 0, 0)      # faint pink halo -> gone
                    cleared += 1
                else:
                    # keep the luminance, drop the magenta: pull blue down to
                    # the warm side so the glow reads as gold, not pink
                    nb = g + (r - g) // 4
                    px[x, y] = (r, g, min(b, nb), a)
                    fixed += 1

    if fixed or cleared:
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
        im.save(path, "PNG", optimize=True)
    return fixed, cleared


def main():
    names = sys.argv[1:]
    files = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".png"):
            continue
        if names and os.path.splitext(fn)[0] not in names:
            continue
        files.append(fn)

    for fn in files:
        fixed, cleared = despill(os.path.join(SRC, fn))
        tag = "clean" if not (fixed or cleared) else "{} recoloured, {} halo removed".format(fixed, cleared)
        print("{:<16} {}".format(os.path.splitext(fn)[0], tag))


if __name__ == "__main__":
    sys.exit(main() or 0)
