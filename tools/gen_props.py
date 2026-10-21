"""Generate the shop props (pizzas, slice, plates, topping box, topping bowls).

Uses the shop reference with Billu as the style guide and runs the requests in
parallel. Output: transparent PNGs in assets/props.

    python -I tools/gen_props.py            # everything not already there
    python -I tools/gen_props.py pizza_slice --force
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_assets import ROOT, generate, key_out, read_key, ref_b64  # noqa: E402

OUT = os.path.join(ROOT, "assets", "props")
REF = "assets/source/refs/shop_with_billu.png"

STYLE = (
    "A single game prop for a children's educational pizza game. Match the attached reference "
    "image's art style exactly (look at the two pizzas on the counter and the pizza slice on the "
    "sign): clean 2D cartoon, smooth soft cel shading, warm dark-brown outlines, bright appetising "
    "colours. Draw ONLY the object described, nothing else from the reference: no cat, no shop, "
    "no counter, no sign, no text, no letters, no logo, no watermark."
)
PLATE = (
    "Seen from a slight three-quarter front angle, centred with a small margin. Isolated on a "
    "completely flat solid pure {name} {hex} background touching all four edges, no table, no "
    "ground, no cast shadow, and no {name} tint anywhere on the object."
)
KEYS = {"magenta": ("magenta", "#FF00FF"), "green": ("chroma green", "#00FF00")}


def prop(desc, key="magenta", w=1024, h=1024):
    name, hx = KEYS[key]
    return dict(key=key, w=w, h=h, keyed=True,
                prompt="{}\n\n{}\n\n{}".format(STYLE, PLATE.format(name=name, hex=hx), desc))


ASSETS = {
    "pizza_board_1": prop("A whole round margherita pizza with a puffy golden crust, melted "
                          "cheese, red tomato slices and a few fresh basil leaves, resting on a "
                          "round wooden serving board with a short handle.", w=1536, h=864),
    "pizza_board_2": prop("A whole round veggie pizza with a puffy golden crust, melted cheese, "
                          "black olive rings, mushroom slices and small red tomato pieces, resting "
                          "on a round wooden serving board.", w=1536, h=864),
    "pizza_slice":   prop("A single triangular slice of pizza, point facing down-left, golden "
                          "crust edge, melted cheese and three round red pepperoni, exactly like "
                          "the slice icon on the reference sign."),
    "plates_stack":  prop("A neat stack of five clean white ceramic dinner plates with a thin "
                          "pale-blue rim."),
    "topping_box":   prop("An open wooden topping box seen from the front and slightly above, "
                          "divided into four square compartments, each filled to the top: red "
                          "tomato slices, white button-mushroom slices, yellow sweet-corn kernels, "
                          "and purple-red onion rings. Chunky warm wood with visible plank lines.",
                          key="green", w=1536, h=864),
    "top_tomato":    prop("A small round wooden bowl filled with fresh red tomato slices."),
    "top_mushroom":  prop("A small round wooden bowl filled with white button-mushroom slices."),
    "top_corn":      prop("A small round wooden bowl filled with bright yellow sweet-corn kernels."),
    "top_onion":     prop("A small round wooden bowl filled with purple-red onion rings.",
                          key="green"),
}


def make(name, key, ref):
    spec = ASSETS[name]
    raw = generate(name, spec, key, ref)
    im = key_out(raw, spec["key"])
    im.thumbnail((900, 900))
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
