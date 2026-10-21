"""Generate the gameplay art: top-down pizzas, mould rims and topping pieces.

The game cuts these up in code, so each image is a clean whole that geometry
can be laid over: pizzas are plain (sauce and cheese, no toppings) and exactly
top-down; mould rims are empty in the middle so the code can draw exact blades.
Output: transparent PNGs in assets/game.

    python -I tools/gen_game_art.py            # everything not already there
    python -I tools/gen_game_art.py pizza_round --force
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_assets import ROOT, generate, key_out, read_key, ref_b64  # noqa: E402

OUT = os.path.join(ROOT, "assets", "game")
REF = "assets/source/refs/shop_with_billu.png"

STYLE = (
    "Game art for a children's fractions game. Match the attached reference image's art style "
    "exactly (look closely at the pizzas on the counter): clean 2D cartoon, smooth soft cel "
    "shading, warm dark-brown outlines, bright appetising colours. Draw ONLY the object "
    "described: no cat, no shop, no counter, no wooden board, no plate, no hands, no text, no "
    "watermark."
)
BACK = (
    "Isolated on a completely flat solid pure {name} {hex} background touching all four edges. "
    "No table, no ground, no cast shadow, no {name} tint anywhere on the object."
)
TOPDOWN = (
    "Viewed from DIRECTLY ABOVE, a perfectly flat orthographic top-down view with no "
    "perspective and no tilt. The object fills the frame almost edge to edge, centred."
)
KEYS = {"magenta": ("magenta", "#FF00FF"), "green": ("chroma green", "#00FF00")}


def art(desc, key="magenta", w=1024, h=1024, topdown=True):
    name, hx = KEYS[key]
    parts = [STYLE, TOPDOWN if topdown else "", BACK.format(name=name, hex=hx), desc]
    return dict(key=key, w=w, h=h, prompt="\n\n".join(p for p in parts if p))


PLAIN = ("A plain cheese pizza with NO toppings at all: a puffy golden-brown baked crust rim, "
         "red tomato sauce peeking through, and evenly melted golden mozzarella with a few soft "
         "browned bubbles. No pepperoni, no vegetables, no herbs, no cuts or slice lines.")

ASSETS = {
    "pizza_round":  art("A perfectly circular round pizza. " + PLAIN),
    "pizza_square": art("A perfectly square pizza with slightly rounded corners. " + PLAIN),
    "pizza_rect":   art("A rectangular pizza about twice as wide as it is tall, slightly "
                        "rounded corners. " + PLAIN, w=1536, h=864),

    "mould_round":  art("A flat circular stainless-steel pizza mould seen EXACTLY from directly "
                        "overhead, so it appears as a perfect flat circle outline: one thick "
                        "polished metal band forming a perfect circle, exactly like the square "
                        "frame mould but round. No visible side wall, no depth, no 3D cylinder, "
                        "no perspective. COMPLETELY EMPTY inside, showing only the flat "
                        "background colour. No blades, no spokes, no handle."),
    "mould_square": art("A square stainless-steel pizza cutting mould: a single thick polished "
                        "metal square frame with slightly rounded corners and soft highlights. "
                        "The frame is COMPLETELY EMPTY inside, showing only the flat background "
                        "colour. No blades, no dividers, no handle."),
    "mould_rect":   art("A rectangular stainless-steel pizza cutting mould, about twice as wide "
                        "as it is tall: a single thick polished metal frame with slightly rounded "
                        "corners. COMPLETELY EMPTY inside, showing only the flat background "
                        "colour. No blades, no dividers, no handle.", w=1536, h=864),

    "board_empty":  art("An empty wooden pizza serving board, rounded paddle shape with a short "
                        "handle on the left that has a small hanging hole, light warm wood with soft "
                        "grain lines. Completely empty, nothing on it.", w=1536, h=1024),
    "pizza_cutter": art("A pizza cutter: a shiny round steel cutting wheel with a small centre "
                        "bolt, attached to a chunky dark teal plastic handle, lying flat, seen from "
                        "directly above."),
    "plate_top":    art("A cute cartoon game icon of an empty serving plate: a cream-white disc "
                        "with a soft inner well and a warm terracotta-orange band around the rim, "
                        "chunky and simple, seen from directly above."),

    "piece_tomato":   art("One single round slice of fresh red tomato, seen from above, with "
                          "its seed pattern visible."),
    "piece_mushroom": art("One single slice of white button mushroom, seen from above, showing "
                          "the classic umbrella cross-section shape."),
    "piece_corn":     art("A small cluster of three plump bright-yellow sweet-corn kernels "
                          "touching each other, seen from above."),
    "piece_onion":    art("A cute cartoon game icon of a curved strip of sliced red onion: a thick "
                          "purple-violet crescent arc with a pale lilac inner layer line, glossy "
                          "highlight, chunky and simple.", key="green"),
}


def make(name, key, ref):
    spec = ASSETS[name]
    raw = generate(name, spec, key, ref)
    im = key_out(raw, spec["key"])
    a = im.getchannel("A").point(lambda v: 0 if v < 40 else v)
    im.putalpha(a)
    if a.getbbox():
        im = im.crop(a.getbbox())
    im.thumbnail((1024, 1024))
    im.save(os.path.join(OUT, name + ".png"), "PNG", optimize=True)
    return "{} {}x{}".format(name, *im.size)


def main():
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a in ASSETS] or list(ASSETS)
    os.makedirs(OUT, exist_ok=True)
    todo = [n for n in names if force or not os.path.exists(os.path.join(OUT, n + ".png"))]
    if not todo:
        print("nothing to do")
        return
    key, ref = read_key(), ref_b64(REF)
    failed = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs = {pool.submit(make, n, key, ref): n for n in todo}
        for fut in as_completed(jobs):
            n = jobs[fut]
            try:
                print("saved", fut.result(), flush=True)
            except Exception as exc:
                print("FAILED", n, str(exc)[:200], flush=True)
                failed.append(n)
    print("done, {} failed{}".format(len(failed), (": " + " ".join(failed)) if failed else ""))


if __name__ == "__main__":
    sys.exit(main() or 0)
