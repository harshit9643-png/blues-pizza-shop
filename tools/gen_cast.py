"""Generate the rest of the cast to match the official character art.

The official characters (assets/source/official) set the style. This script
fills in the customers that have no official art yet, and Noori from her
character sheet. Output lands in assets/characters as transparent PNG.

    python -I tools/gen_cast.py --list
    python -I tools/gen_cast.py monty tez
    python -I tools/gen_cast.py --all          # skips anything already there
    python -I tools/gen_cast.py noori --force
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_assets import ROOT, generate, key_out, read_key, ref_b64  # noqa: E402

OUT = os.path.join(ROOT, "assets", "characters")
LINEUP = "assets/source/refs/style_lineup.png"
NOORI_SHEET = "assets/source/official/noori_character_sheet.png"

STYLE = (
    "Children's educational game character. Match the attached line-up of characters EXACTLY "
    "in art style so the new character sits in the same cast: clean flat 2D cartoon, smooth "
    "cel shading with only very soft gradients, warm dark-brown outlines of even medium weight, "
    "big round brown eyes with white catchlights, a cream or lighter-toned belly or muzzle, "
    "chunky friendly proportions with a large head, a wide happy open smile. Draw ONE character "
    "only, never copy the reference characters. No text, no letters, no logo, no watermark."
)

POSE = (
    "Full body, standing upright on two feet, facing the viewer, centred with a small margin, "
    "in a relaxed confident pose like the reference characters (hands on hips or at the sides). "
    "Isolated on a completely flat solid pure {name} {hex} background touching all four edges. "
    "No ground, no cast shadow, no gradient in the background, and no {name} tint on the "
    "character."
)
KEYS = {"magenta": ("magenta", "#FF00FF"), "green": ("chroma green", "#00FF00")}


def cast(desc, key="magenta", ref=LINEUP, style=STYLE):
    name, hx = KEYS[key]
    return dict(ref=ref, key=key, keyed=True, w=1024, h=1024,
                prompt="{}\n\n{}\n\n{}".format(style, POSE.format(name=name, hex=hx), desc))


NOORI_STYLE = (
    "Draw the EXACT character shown on the attached character consistency sheet: Noori, a wise, "
    "kind, elderly granny snowy owl. Soft white fluffy feathers with faint pale grey-lilac shading, "
    "a white feather bun on top of her head held by a purple (#6A2CA0) headband, round thin gold "
    "glasses, a small golden-yellow beak, golden-orange feet, half-lidded gentle eyes, and a "
    "brown wooden walking cane. Same clean 2D cartoon line style, same proportions and same "
    "colours as the sheet. Draw ONE full-body pose only, no sheet layout, no labels, no text, "
    "no colour swatches."
)

ASSETS = {
    "monty":   cast("A cheeky brown monkey with a cream face, cream belly and big round cream "
                    "ears, a long curly tail, waving hello with one hand and the other on his hip."),
    "tez":     cast("Tez, a slow gentle tortoise standing upright on two short legs, a domed "
                    "brown and amber patterned shell on his back, green-grey skin, droopy calm "
                    "eyelids and a patient contented smile."),
    "bijli":   cast("Bijli, a lively bright lime-green snake coiled upright into a neat spiral so "
                    "she stands tall, a pale yellow belly, tiny forked tongue, big eyes and a "
                    "mischievous grin. A snake has no arms or legs."),
    "badal":   cast("Badal, a calm teal-blue snake coiled upright into a neat spiral so he stands "
                    "tall, a pale cream belly, big kind eyes and a gentle smile. Same body shape "
                    "as a twin snake, only the colour differs. A snake has no arms or legs."),
    "madhu":   cast("Madhu, a tiny round fuzzy bumblebee with yellow and dark-brown stripes, "
                    "small translucent wings, two antennae, enormous sweet eyes, standing on two "
                    "little legs with her hands on her hips."),
    "jhumru":  cast("Jhumru, a big gentle grey elephant calf with huge floppy pink-lined ears, a "
                    "trunk curled up in greeting, small white tusks, a cream tummy and a warm "
                    "friendly smile."),
    "giraffe": cast("A tall golden-yellow giraffe with brown patches, a long neck, two small "
                    "ossicone horns, long eyelashes and a polite happy smile, standing upright on "
                    "two legs with hands at her sides."),
    "parrot":  cast("A vivid green parrot with red and yellow wing tips, a curved orange beak, "
                    "a cheeky tilted head and a chirpy smile, standing upright with wings on hips."),

    "noori":       cast("She stands calmly leaning on her wooden cane with one wing, the other "
                        "wing raised slightly in a warm welcoming gesture, a kind gentle smile.",
                        key="green", ref=NOORI_SHEET, style=NOORI_STYLE),
    "noori_point": cast("She is explaining a lesson: one wing raised with a feather-tip pointing "
                        "up as if making a wise point, the other wing holding her wooden cane, "
                        "a knowing encouraging smile.",
                        key="green", ref=NOORI_SHEET, style=NOORI_STYLE),
}


def main():
    args = sys.argv[1:]
    if "--list" in args:
        print("\n".join(ASSETS))
        return
    names = list(ASSETS) if "--all" in args else [a for a in args if a in ASSETS]
    if not names:
        print("pass asset names or --all")
        return 1
    key = read_key()
    os.makedirs(OUT, exist_ok=True)
    failed = []
    for i, name in enumerate(names, 1):
        path = os.path.join(OUT, name + ".png")
        if os.path.exists(path) and "--force" not in args:
            print("[{}/{}] {} — already there, skipping".format(i, len(names), name), flush=True)
            continue
        print("[{}/{}] {} …".format(i, len(names), name), flush=True)
        spec = ASSETS[name]
        try:
            raw = generate(name, spec, key, ref_b64(spec["ref"]))
            im = key_out(raw, spec["key"])
            im.thumbnail((900, 900))
            im.save(path, "PNG", optimize=True)
            print("        saved {} ({}x{})".format(name + ".png", *im.size), flush=True)
        except Exception as exc:
            print("        FAILED: {}".format(exc)[:300], flush=True)
            failed.append(name)
        time.sleep(2)
    print("\ndone, {} failed{}".format(len(failed), (": " + " ".join(failed)) if failed else ""))


if __name__ == "__main__":
    sys.exit(main() or 0)
