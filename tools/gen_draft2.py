"""Generate the Draft 2 art set: block-print tablecloth, cutting board, steel
thali and steel katori bowls of toppings. Output: assets/draft2/.

Retries a refused image once on the flash model (the pro model sometimes
declines plain household objects as "recitation").

    python -I tools/gen_draft2.py
    python -I tools/gen_draft2.py cloth --force
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_assets  # noqa: E402
from gen_assets import ROOT, key_out, read_key, ref_b64  # noqa: E402

OUT = os.path.join(ROOT, "assets", "draft2")
REF = "assets/source/refs/shop_with_billu.png"

STYLE = (
    "Art for a children's fractions game. Match the attached reference image's art style: clean "
    "2D cartoon, smooth soft cel shading, warm dark-brown outlines, bright friendly colours. Draw "
    "ONLY the object described: no cat, no shop, no people, no hands, no text, no watermark."
)
TOP = ("Viewed from DIRECTLY ABOVE, flat orthographic top-down view, no perspective, centred, "
       "filling the frame with a small margin.")
BACK = ("Isolated on a completely flat solid pure {name} {hex} background touching all four edges, "
        "no table, no cast shadow, no {name} tint on the object.")
KEYS = {"magenta": ("magenta", "#FF00FF"), "green": ("chroma green", "#00FF00")}


def obj(desc, key="magenta", w=1024, h=1024):
    name, hx = KEYS[key]
    return dict(key=key, keyed=True, w=w, h=h,
                prompt="\n\n".join([STYLE, TOP, BACK.format(name=name, hex=hx), desc]))


ASSETS = {
    "cloth": dict(keyed=False, w=1024, h=1024, prompt=(
        "A flat, evenly lit, straight-on scan of fabric that fills the ENTIRE image edge to edge: a "
        "hand block-printed Indian cotton tablecloth in the Sanganeri and Bagru style. Warm cream "
        "cotton ground with a visible soft weave. Small, sparse, softly faded indigo-blue floral "
        "buttis (little five-petal flowers with two tiny leaves) placed in a regular staggered grid "
        "with generous cream space between them, plus tiny indigo dots between the flowers. Gentle "
        "hand-printed imperfections. Seamless repeating textile pattern. No folds, no shadows, no "
        "objects, no border, no frame, no text.")),
    "board_square": obj("A large square wooden cutting board with softly rounded corners, made of "
                        "warm honey-coloured wooden planks glued edge to edge with visible soft grain, "
                        "slightly darker rim edge. Completely empty."),
    "thali": obj("A large round polished stainless-steel thali plate with a low raised rim and soft "
                 "silver highlights. Completely empty."),
    "katori_tomato":   obj("A small round polished stainless-steel katori bowl, filled to the brim "
                           "with fresh red tomato slices."),
    "katori_mushroom": obj("A small round polished stainless-steel katori bowl, filled to the brim "
                           "with white button-mushroom slices."),
    "katori_corn":     obj("A small round polished stainless-steel katori bowl, filled to the brim "
                           "with bright yellow sweet-corn kernels."),
    "katori_onion":    obj("A small round polished stainless-steel katori bowl, filled to the brim "
                           "with purple-red onion rings.", key="green"),
}


def make(name, key, ref, model=None):
    spec = ASSETS[name]
    if model:
        gen_assets.MODEL = model
    raw = gen_assets.generate(name, spec, key, ref)
    path = os.path.join(OUT, name + ".png")
    if spec["keyed"]:
        im = key_out(raw, spec["key"])
        a = im.getchannel("A").point(lambda v: 0 if v < 40 else v)
        im.putalpha(a)
        im = im.crop(a.getbbox())
        im.thumbnail((1100, 1100))
        im.save(path, "PNG", optimize=True)
    else:
        from PIL import Image
        import io
        Image.open(io.BytesIO(raw)).convert("RGB").save(path, "PNG", optimize=True)
    return name


def main():
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a in ASSETS] or list(ASSETS)
    os.makedirs(OUT, exist_ok=True)
    todo = [n for n in names if force or not os.path.exists(os.path.join(OUT, n + ".png"))]
    key, ref = read_key(), ref_b64(REF)
    failed = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs = {pool.submit(make, n, key, ref): n for n in todo}
        for fut in as_completed(jobs):
            n = jobs[fut]
            try:
                print("saved", fut.result(), flush=True)
            except Exception as exc:
                print("refused/failed", n, str(exc)[:120], flush=True)
                failed.append(n)
    still = []
    for n in failed:                      # one retry on the flash model
        try:
            print("saved (flash)", make(n, key, ref, model="gemini-3.1-flash-image"), flush=True)
        except Exception as exc:
            print("FAILED", n, str(exc)[:160], flush=True)
            still.append(n)
    print("done, {} failed{}".format(len(still), (": " + " ".join(still)) if still else ""))


if __name__ == "__main__":
    sys.exit(main() or 0)
