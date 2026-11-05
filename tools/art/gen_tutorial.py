"""Generate the tutorial scroll art: a wooden roller hung on a rope, and the parchment sheet.
Output: assets/tutorial/.

    python -I tools/gen_tutorial.py
    python -I tools/gen_tutorial.py rod_top --force
"""

import io
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_assets  # noqa: E402
from gen_assets import ROOT, key_out, read_key, ref_b64  # noqa: E402

OUT = os.path.join(ROOT, "assets", "tutorial")
REF = "assets/web/backdrop.webp"

STYLE = (
    "Art for a children's fractions game set in a jungle pizza shop. Match the colours and friendly "
    "finish of the attached reference image (warm honey browns, cream, leaf green), but render the "
    "object as a polished, rich 3D game asset: soft volumetric lighting from the upper left, smooth "
    "rounded forms, gentle specular highlights, subtle ambient occlusion, like a premium mobile game "
    "UI prop. Draw ONLY the object described: no cat, no shop, no people, no hands, no text, no "
    "letters, no numbers, no watermark, no frame."
)
BACK = ("Isolated on a completely flat solid pure {name} {hex} background touching all four edges, no "
        "floor, no cast shadow, and none of the {name} may tint the object.")
KEYS = {"magenta": ("magenta", "#FF00FF"), "green": ("chroma green", "#00FF00")}


def obj(desc, key="magenta"):
    name, hx = KEYS[key]
    return dict(key=key, keyed=True, w=1600, h=900, prompt="\n\n".join([STYLE, BACK.format(name=name, hex=hx), desc]))


ASSETS = {
    "rod_top": obj(
        "Seen straight from the front: ONE long horizontal cylindrical wooden scroll roller that spans "
        "almost the full width of the image, polished warm walnut wood with a soft sheen and fine grain, "
        "and an ornate rounded golden-brass knob cap on each end. A thick twisted natural jute rope is "
        "tied round the roller near each end; the two rope ends rise diagonally and meet at the top centre "
        "of the image in a small brass ring, forming a wide triangle, as if the roller hangs from a hook. "
        "The rope reaches the top edge of the image. The roller sits in the lower third of the image."),
    "rod_bottom": obj(
        "Seen straight from the front: ONE long horizontal cylindrical wooden scroll roller that spans "
        "almost the full width of the image, polished warm walnut wood with a soft sheen and fine grain, "
        "and an ornate rounded golden-brass knob cap on each end. A thin edge of rolled cream parchment "
        "is wrapped round the middle of the roller. Nothing else: no rope. Centred vertically."),
    "parchment": dict(keyed=False, w=1600, h=900, prompt=(
        STYLE + "\n\nA flat, evenly lit, straight-on view of one large sheet of old cream parchment paper "
        "that fills the ENTIRE image edge to edge: warm ivory colour, soft fibrous paper texture, very "
        "gentle darker toasted tint towards the left and right edges, a few faint soft stains, a slim "
        "hand-painted border of tiny green jungle leaves and vines running down ONLY the left and right "
        "edges. The large middle area is plain, light and calm so text and pictures can be placed on it. "
        "No folds, no rollers, no top or bottom border, no text.")),
}


def make(name, key, ref, model=None):
    from PIL import Image
    spec = ASSETS[name]
    if model:
        gen_assets.MODEL = model
    raw = gen_assets.generate(name, spec, key, ref)
    if spec["keyed"]:
        im = key_out(raw, spec["key"])
        a = im.getchannel("A").point(lambda v: 0 if v < 40 else v)
        im.putalpha(a)
        im = im.crop(a.getbbox())
        im.thumbnail((2000, 2000))
        im.save(os.path.join(OUT, name + ".webp"), "WEBP", quality=90, method=6)
    else:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((1920, 1920))
        im.save(os.path.join(OUT, name + ".webp"), "WEBP", quality=86, method=6)
    im.save(os.path.join(OUT, name + "_src.png"))
    return name


def main():
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a in ASSETS] or list(ASSETS)
    os.makedirs(OUT, exist_ok=True)
    todo = [n for n in names if force or not os.path.exists(os.path.join(OUT, n + ".webp"))]
    key, ref = read_key(), ref_b64(REF)
    failed = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(make, n, key, ref): n for n in todo}
        for fut in as_completed(jobs):
            n = jobs[fut]
            try:
                print("saved", fut.result(), flush=True)
            except Exception as exc:
                print("refused/failed", n, str(exc)[:160], flush=True)
                failed.append(n)
    for n in failed:                      # one retry on the flash model
        try:
            print("saved (flash)", make(n, key, ref, model="gemini-3.1-flash-image"), flush=True)
        except Exception as exc:
            print("FAILED", n, str(exc)[:200], flush=True)


if __name__ == "__main__":
    main()
