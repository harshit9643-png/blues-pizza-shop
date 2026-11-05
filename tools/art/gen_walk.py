"""Generate side-view walk cycles (character sheets) for the story with the Gemini image API.

Each character's front-view art is sent as the reference, so the side view keeps its exact look.
The model draws 4 walk poses in one row on flat magenta; the row is keyed out and cut into
frames: assets/story/walk/<name>_0.webp ... _3.webp (all facing right, feet on the bottom edge).

    python -I tools/gen_walk.py                 # every character
    python -I tools/gen_walk.py monty --force   # just one, again
"""

import base64
import io
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_assets  # noqa: E402
from gen_assets import ROOT, key_out, read_key  # noqa: E402

OUT = os.path.join(ROOT, "assets", "story", "walk")
CHARS = {
    "billu": ("billu_happy", "a grey cat chef in an oversized white chef's hat, red neckerchief, cream apron, brown trousers"),
    "monty": ("monty", "a brown cartoon monkey with a cream face and belly and a long curly tail"),
    "rabbit": ("rabbit", "a cream-white cartoon rabbit with long pink-lined ears"),
    "ant": ("ant", "a red-orange cartoon ant with big eyes, two antennae and six thin legs"),
}
PROMPT = (
    "Character sheet for a children's game: the SAME character as in the attached image, {desc}. Keep its "
    "exact colours, proportions, outline style, soft cel shading and friendly happy face. Draw it FOUR times "
    "in one horizontal row, evenly spaced, every pose in clean SIDE VIEW (profile, facing RIGHT), showing a "
    "smooth friendly walk cycle: (1) contact - front foot forward, heel down, back foot behind; (2) down - "
    "weight on the front leg, body slightly lower; (3) passing - legs together under the body, body highest; "
    "(4) up - back leg pushing off, the other leg swinging forward. Arms swing opposite to the legs. All four "
    "the same size with their feet on the same ground line. Isolated on a completely flat solid pure magenta "
    "#FF00FF background touching all four edges; no ground, no shadow, no text, no numbers, no frame, and no "
    "magenta tint on the character."
)


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def split_row(im, n=4):
    """Cut a keyed row of n poses into n frames, by the gaps between the figures."""
    from PIL import Image
    a = im.getchannel("A")
    W, H = im.size
    cols = [sum(1 for y in range(0, H, 2) if a.getpixel((x, y)) > 40) for x in range(W)]
    filled = [c > 2 for c in cols]
    runs, start = [], None
    for x, f in enumerate(filled + [False]):
        if f and start is None:
            start = x
        elif not f and start is not None:
            runs.append([start, x])
            start = None
    while len(runs) > n:                      # merge the closest neighbours (a tail or a hand split off)
        gaps = [runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]
        i = gaps.index(min(gaps))
        runs[i:i + 2] = [[runs[i][0], runs[i + 1][1]]]
    if len(runs) != n:
        raise ValueError("found {} figures, expected {}".format(len(runs), n))
    frames = [im.crop((x0, 0, x1, H)) for x0, x1 in runs]
    boxes = [f.getchannel("A").getbbox() for f in frames]
    top = min(b[1] for b in boxes)
    bottom = max(b[3] for b in boxes)
    width = max(b[2] - b[0] for b in boxes)
    out = []
    for f, b in zip(frames, boxes):              # same canvas for every frame, feet on the bottom edge
        c = Image.new("RGBA", (width + 8, bottom - top + 4), (0, 0, 0, 0))
        c.alpha_composite(f.crop((b[0], top, b[2], bottom)), ((width + 8 - (b[2] - b[0])) // 2, 2))
        out.append(c)
    return out


def make(name, key):
    src, desc = CHARS[name]
    from PIL import Image
    buf = io.BytesIO()                       # the API call sends the reference as PNG
    Image.open(os.path.join(ROOT, "assets", "web", src + ".webp")).save(buf, "PNG")
    ref = base64.b64encode(buf.getvalue()).decode()
    spec = dict(keyed=True, key="magenta", w=1600, h=900, prompt=PROMPT.format(desc=desc))
    raw = gen_assets.generate(name, spec, key, ref)
    im = key_out(raw, "magenta")
    im.save(os.path.join(OUT, name + "_sheet.png"))
    frames = split_row(im)
    h = 512
    for i, f in enumerate(frames):
        f = f.resize((round(f.width * h / f.height), h))
        f.save(os.path.join(OUT, "{}_{}.webp".format(name, i)), "WEBP", quality=90)
    return name, frames[0].width / frames[0].height


def main():
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a in CHARS] or list(CHARS)
    os.makedirs(OUT, exist_ok=True)
    todo = [n for n in names if force or not os.path.exists(os.path.join(OUT, n + "_0.webp"))]
    key = read_key()
    man_path = os.path.join(OUT, "manifest.json")
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for fut in as_completed({pool.submit(make, n, key): n for n in todo}):
            try:
                n, ar = fut.result()
                man[n] = {"frames": 4, "aspect": round(ar, 4)}
                print("saved", n, flush=True)
            except Exception as exc:
                print("FAILED", str(exc)[:200], flush=True)
    json.dump(man, open(man_path, "w"), indent=1)
    print("manifest:", man)


if __name__ == "__main__":
    main()
