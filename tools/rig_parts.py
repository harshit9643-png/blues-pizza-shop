"""Cut puppet parts out of the character art for the story animations: an arm that can rotate at
the shoulder (Billu holding the cutter, Monty waving). Output: assets/story/.

    python -I tools/rig_parts.py
"""
import json
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "web")
OUT = os.path.join(ROOT, "assets", "story")

# polygons in fractions of the image: "cut" is removed from the body, "arm" (a little bigger, so it
# overlaps the body at the shoulder) becomes the separate arm
PARTS = {
    "billu": dict(src="billu_happy", pivot=(0.645, 0.47),
                  cut=[(0.80, 0.19), (1.0, 0.19), (1.0, 0.36), (0.70, 0.53), (0.645, 0.53), (0.665, 0.42), (0.74, 0.34), (0.80, 0.29)],
                  arm=[(0.80, 0.19), (1.0, 0.19), (1.0, 0.36), (0.70, 0.55), (0.60, 0.55), (0.62, 0.42), (0.73, 0.33), (0.80, 0.29)]),
    "monty": dict(src="monty", pivot=(0.30, 0.54),
                  cut=[(0.0, 0.27), (0.16, 0.27), (0.16, 0.31), (0.215, 0.31), (0.215, 0.45), (0.30, 0.50), (0.31, 0.63), (0.0, 0.63)],
                  arm=[(0.0, 0.27), (0.16, 0.27), (0.16, 0.31), (0.215, 0.31), (0.215, 0.44), (0.33, 0.49), (0.345, 0.64), (0.0, 0.64)]),
}


def mask(size, poly, blur=0):
    w, h = size
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([(x * w, y * h) for x, y in poly], fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for name, p in PARTS.items():
        im = Image.open(os.path.join(SRC, p["src"] + ".webp")).convert("RGBA")
        a = im.getchannel("A")
        body = im.copy()
        body.putalpha(Image.composite(Image.new("L", im.size, 0), a, mask(im.size, p["cut"], 1)))
        body.save(os.path.join(OUT, name + "_body.webp"), "WEBP", quality=92)
        arm = im.copy()
        arm.putalpha(Image.composite(a, Image.new("L", im.size, 0), mask(im.size, p["arm"], 1)))
        box = arm.getchannel("A").getbbox()
        arm.crop(box).save(os.path.join(OUT, name + "_arm.webp"), "WEBP", quality=92)
        W, H = im.size
        meta[name] = dict(box=[round(box[0] / W, 4), round(box[1] / H, 4), round((box[2] - box[0]) / W, 4), round((box[3] - box[1]) / H, 4)],
                          pivot=p["pivot"])
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
