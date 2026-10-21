"""Generate Billu's Pizza Kitchen art assets with the Gemini image API.

Every call is seeded with the reference painting so the whole cast shares one
finish. Characters are rendered on flat magenta and keyed out to transparent
PNG; the backdrop is kept opaque.

    python -I tools/gen_assets.py --list
    python -I tools/gen_assets.py billu_idle backdrop
    python -I tools/gen_assets.py --all
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")


def dest_dir(name):
    """assets/backgrounds, assets/props or assets/characters, by asset kind."""
    if name == "backdrop":
        return os.path.join(OUT, "backgrounds")
    if name in ("trophy", "medal"):
        return os.path.join(OUT, "props")
    return os.path.join(OUT, "characters")
KEY_FILE = os.environ.get(
    "GEMINI_KEY_FILE",
    r"C:\Users\Lenovo\AppData\Local\Temp\claude\c--Users-Lenovo-Downloads-Billu-pizza-shop"
    r"\9cd5f55a-8dea-4359-9bd2-12c37aa50555\scratchpad\gemini.key",
)
REF = os.environ.get(
    "BILLU_REF",
    r"C:\Users\Lenovo\AppData\Local\Temp\claude\c--Users-Lenovo-Downloads-Billu-pizza-shop"
    r"\9cd5f55a-8dea-4359-9bd2-12c37aa50555\images\2.png",
)
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}"

# --------------------------------------------------------------------------
# style
# --------------------------------------------------------------------------

STYLE = (
    "Children's educational mobile-game art, 2D cartoon illustration in a soft painterly style. "
    "Match the attached reference image exactly: the same airbrushed cel shading with smooth "
    "gradients, the same thick rounded forms, soft warm dark-brown outlines rather than harsh "
    "black ink, big glossy expressive eyes with bright white catchlights, chunky simplified "
    "shapes, gentle ambient occlusion. Warm saturated palette of honey browns, leaf greens, "
    "terracotta, cream and sky blue. Friendly, wholesome, suitable for 7 year olds. "
    "No text, no letters, no numbers, no logo, no watermark, no frame or border, no signature."
)

CUTOUT = (
    "Full body, standing upright, facing the viewer, centred in frame with a small margin. "
    "Slightly oversized head, short rounded body, chibi game-mascot proportions. "
    "Isolated on a completely flat solid pure {name} {hex} background. "
    "No ground, no cast shadow, no reflection, no vignette, no gradient in the background. "
    "The {name} must be one single flat colour touching all four edges, and none of that "
    "{name} may tint, glow onto or blend into the character itself."
)

KEYS = {"magenta": ("magenta", "#FF00FF"), "green": ("chroma green", "#00FF00")}


def char(desc, key="magenta"):
    name, hx = KEYS[key]
    return "{}\n\n{}\n\n{}".format(STYLE, CUTOUT.format(name=name, hex=hx), desc)


def char2(desc):
    """Character on the green plate — for glowing assets that bleed into magenta."""
    return char(desc, "green")


ASSETS = {
    # ---- backdrop -------------------------------------------------------
    "backdrop": dict(
        w=1536, h=864, keyed=False,
        prompt=STYLE + "\n\n"
        "Wide empty establishing shot of a jungle pizza stall, recreated from the reference "
        "image but with NO cat and NO characters anywhere. A wooden market stall with a roof "
        "made of big overlapping green leaves, a wood-fired terracotta brick oven glowing "
        "orange inside it, a long cream-coloured counter that is completely empty and clear, "
        "a wooden shelf with a stack of white plates, a blank wooden signboard above with "
        "absolutely no writing on it. Dense bright jungle and palm trees behind, a small "
        "thatched hut far on the left, blue sky with soft white clouds. Warm packed-earth "
        "ground in the foreground with two small round wooden tables and child-sized chairs, "
        "one group on the left and one on the right, leaving the centre of the ground open "
        "and empty. Bright midday lighting, cheerful and inviting.",
    ),

    # ---- hosts ----------------------------------------------------------
    "billu_happy": dict(w=1024, h=1024, ref="refs/billu_on_magenta.png", prompt=char(
        "The EXACT same character as the attached reference image, matched precisely: a grey cat with cream muzzle, chest and paws, pink inner ears, amber-gold eyes, a tall cream chef's hat, a red neckerchief tied at the neck, a cream bib apron with a front pocket and two gold buttons on the straps, rolled-up brown trousers, and a fluffy grey tail with a cream tip. Same proportions, same outline weight, same colours. "
        "Now he is cheering with both paws thrown up in the air, eyes squeezed happy and "
        "mouth wide open in delight, tail curled up. Pure joy and celebration.")),

    "billu_puzzled": dict(w=1024, h=1024, ref="refs/billu_on_magenta.png", prompt=char(
        "The EXACT same character as the attached reference image, matched precisely: a grey cat with cream muzzle, chest and paws, pink inner ears, amber-gold eyes, a tall cream chef's hat, a red neckerchief tied at the neck, a cream bib apron with a front pocket and two gold buttons on the straps, rolled-up brown trousers, and a fluffy grey tail with a cream tip. Same proportions, same outline weight, same colours. "
        "Now he is confused: head tilted, one paw scratching the side of his chef's hat, "
        "eyebrows raised, a small awkward uncertain smile, the other paw hanging at his side.")),

    "noori": dict(w=1024, h=1024, key="green", prompt=char2(
        "A small glowing firefly light-sprite, the gentle teacher guide. Her body is soft "
        "cream and pale mint-teal, NOT yellow, with NO bee stripes of any kind. She has a "
        "rounded lantern-like lower body that glows warm white-gold from within like a little "
        "lamp, four delicate translucent pale-blue dragonfly wings, two fine antennae tipped "
        "with tiny soft white light beads, large kind eyes with long lashes and a gentle "
        "knowing smile. A halo of warm light and a few floating sparkles surround her. "
        "She hovers with both small arms open in a warm welcoming gesture. "
        "She must look clearly like a magical firefly lantern spirit, never like a bumblebee.")),

    "noori_point": dict(w=1024, h=1024, key="green", prompt=char2(
        "The same cream and pale mint-teal glowing firefly light-sprite with a warm glowing "
        "lantern body, four translucent pale-blue dragonfly wings, white-tipped antennae and "
        "a halo of soft light. NO yellow and black bee stripes anywhere. She hovers and points "
        "forward with one small arm while the other rests at her side, with a patient, "
        "encouraging teacherly expression, as if explaining something to a child.")),

    # ---- customers ------------------------------------------------------
    "monty":    dict(prompt=char("A playful brown monkey with a cream face and belly, a long "
                "curly tail, big round ears, a wide cheeky grin showing his teeth, one arm "
                "raised waving hello.")),
    "ant":      dict(prompt=char("A tiny but confident dark red ant with three body segments, "
                "six slim legs, two bent antennae, a big friendly smile and huge bright eyes. "
                "Small and plucky.")),
    "tez":      dict(prompt=char("A slow gentle tortoise with a domed brown and amber patterned "
                "shell, wrinkly green-grey skin, a long neck, droopy sleepy eyelids and a "
                "patient contented smile.")),
    "squirrel": dict(prompt=char("A quick orange-brown squirrel with a huge bushy curled tail, "
                "tufted ears, cheeks puffed out full of nuts, bright alert eyes, standing on "
                "its hind legs looking eager and hungry.")),
    "bijli":    dict(prompt=char("A cheerful bright green snake coiled upright into a neat "
                "spiral so it stands, a pale yellow belly, a small forked tongue poking out, "
                "big friendly eyes and a wide smile. Lively and mischievous.")),
    "badal":    dict(prompt=char("A cheerful teal-blue snake coiled upright into a neat spiral "
                "so it stands, a pale cream belly, a small forked tongue poking out, big "
                "friendly eyes and a gentle smile. The calm twin of a green snake.")),
    "madhu":    dict(prompt=char("A tiny round bumblebee with fuzzy yellow and black stripes, "
                "small translucent wings mid-buzz, delicate antennae, enormous sparkling eyes "
                "and a sweet little smile. Hovering just above the ground.")),
    "peacock":  dict(prompt=char("A proud peacock with an iridescent blue body and neck, a "
                "small crown of feathers on his head, his magnificent green and gold eyed tail "
                "fanned out wide behind him, chest puffed, a smug confident smile.")),
    "jhumru":   dict(prompt=char("A big gentle grey elephant with enormous floppy ears, a long "
                "curling trunk raised in greeting, small tusks, round kind eyes and a warm "
                "friendly smile. Heavy but sweet-natured.")),
    "giraffe":  dict(prompt=char("A tall golden-yellow giraffe with soft brown patches, a very "
                "long neck, two small ossicone horns, long eyelashes over big gentle eyes and a "
                "polite happy smile.")),
    "parrot":   dict(prompt=char("A vivid green parrot with a red and yellow patch on its wing, "
                "a curved orange beak, a cheeky tilted head, bright round eyes and a chirpy "
                "expression, perched upright.")),
    "frog":     dict(prompt=char("A bright green frog with a cream belly, huge bulging eyes on "
                "top of his head, wide webbed feet, mid-hop with a big goofy grin.")),
    "gorilla":  dict(prompt=char("A large friendly dark grey gorilla with broad shoulders, a "
                "wide flat nose, one fist thumping his chest proudly, a big good-natured grin "
                "and warm brown eyes. Strong but gentle.")),
    "mouse":    dict(prompt=char("A tiny grey mouse with enormous round pink-lined ears, a long "
                "thin pink tail, tiny whiskers, huge shiny black eyes and a sweet timid smile.")),
    "croc":     dict(prompt=char("A grinning green crocodile with a long snout full of friendly "
                "blunt white teeth, bumpy scaly back, a pale yellow belly, small raised arms and "
                "a cheeky mischievous expression. Toothy but not scary.")),
    "rabbit":   dict(prompt=char("A fluffy white and grey rabbit with very long upright ears, a "
                "round cotton tail, soft pink nose twitching, big bright eyes and a happy "
                "bouncy pose mid-hop.")),
    "bear":     dict(prompt=char("A big round brown bear with a lighter tan muzzle, small round "
                "ears, a chunky belly, a broad sleepy smile and warm friendly eyes, paws resting "
                "on his tummy.")),
    "sloth":    dict(prompt=char("A very slow shaggy grey-brown sloth with long curved arms, a "
                "pale face with dark eye patches, a permanent dreamy half-asleep smile, moving "
                "in extreme slow motion.")),
    "hippo":    dict(prompt=char("An enormous round purple-grey hippo with a huge wide mouth "
                "open in a happy grin, tiny ears, little nostrils on top of her snout, short "
                "stubby legs and a cheerful good-humoured face.")),

    # ---- props ----------------------------------------------------------
    "trophy":   dict(prompt=char("A shiny golden trophy shaped like a round pizza cutter wheel "
                "mounted on a small marble and gold base, gleaming with bright highlights and "
                "little sparkles around it. No text engraved on it.")),
    "medal":    dict(prompt=char("A single shiny gold winner's medal, a round gold disc with a "
                "star pressed into the centre, hanging from a short red and white striped "
                "ribbon. Bright metallic highlights. No text or numbers on it.")),
}

for _a in ASSETS.values():
    _a.setdefault("w", 1024)
    _a.setdefault("h", 1024)
    _a.setdefault("keyed", True)
    _a.setdefault("key", "magenta")


# --------------------------------------------------------------------------
# api
# --------------------------------------------------------------------------

def read_key():
    with open(KEY_FILE) as fh:
        return fh.read().strip()


def ref_b64(path=None):
    path = path or REF
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def generate(name, spec, key, ref, attempt=1):
    body = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": spec["prompt"]},
                {"inline_data": {"mime_type": "image/png", "data": ref}},
            ],
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9" if spec["w"] > spec["h"] else "1:1"},
        },
    }
    req = urllib.request.Request(
        URL.format(MODEL, key),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:400]
        if e.code in (429, 500, 503) and attempt < 4:
            wait = 12 * attempt
            print("  retry {} in {}s ({})".format(attempt, wait, e.code), flush=True)
            time.sleep(wait)
            return generate(name, spec, key, ref, attempt + 1)
        raise RuntimeError("HTTP {} for {}: {}".format(e.code, name, detail))

    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                return base64.b64decode(blob["data"])
    raise RuntimeError("no image returned for {}: {}".format(name, json.dumps(data)[:400]))


# --------------------------------------------------------------------------
# magenta key-out
# --------------------------------------------------------------------------

def key_out(png_bytes, key="magenta"):
    """Flat magenta -> transparent, with spill suppression and a soft edge."""
    from PIL import Image, ImageFilter
    import io

    im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    px = im.load()
    w, h = im.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # magenta-ness: strong red and blue, weak green
            if key == "green":
                hit = g > 120 and g > r + 50 and g > b + 50
                spill = (g - max(r, b)) / 255.0 if hit else 0.0
            else:
                hit = r > 120 and b > 120 and g < min(r, b) - 40
                spill = (min(r, b) - g) / 255.0 if hit else 0.0
            if hit:
                alpha = int(max(0.0, 1.0 - spill * 2.0) * 255)
                if alpha == 0:
                    px[x, y] = (0, 0, 0, 0)
                elif key == "green":
                    px[x, y] = (r, min(g, max(r, b)), b, alpha)
                else:
                    mid = (r + b) // 2
                    px[x, y] = (min(r, mid), g, min(b, mid), alpha)

    # trim to content, then soften the cut edge by one pixel
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    alpha = im.getchannel("A").filter(ImageFilter.GaussianBlur(0.6))
    im.putalpha(alpha)
    return im


def save(name, spec, raw):
    folder = dest_dir(name)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name + ".png")
    if spec["keyed"]:
        im = key_out(raw, spec.get("key", "magenta"))
        # characters never need to be larger than this on screen
        im.thumbnail((640, 640))
        im.save(path, "PNG", optimize=True)
    else:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((1600, 1600))
        im.save(path, "JPEG", quality=86, optimize=True)
        path = path[:-4] + ".jpg"
        im.save(path, "JPEG", quality=86, optimize=True)
        os.remove(os.path.join(folder, name + ".png"))
    return path, os.path.getsize(path)


def main():
    args = [a for a in sys.argv[1:]]
    if "--list" in args:
        for n in ASSETS:
            print(n)
        return
    names = list(ASSETS) if "--all" in args else [a for a in args if a in ASSETS]
    unknown = [a for a in args if a not in ASSETS and not a.startswith("--")]
    if unknown:
        print("unknown assets:", ", ".join(unknown))
        return 1
    if not names:
        print("nothing to do; pass asset names or --all")
        return 1

    key, ref = read_key(), ref_b64()
    ok, failed = 0, []
    for i, name in enumerate(names, 1):
        dest = os.path.join(dest_dir(name), name + ".png")
        dest_j = os.path.join(dest_dir(name), name + ".jpg")
        if "--force" not in args and (os.path.exists(dest) or os.path.exists(dest_j)):
            print("[{}/{}] {} — already there, skipping".format(i, len(names), name), flush=True)
            ok += 1
            continue
        print("[{}/{}] {} …".format(i, len(names), name), flush=True)
        try:
            spec = ASSETS[name]
            raw = generate(name, spec, key, ref_b64(spec["ref"]) if spec.get("ref") else ref)
            path, size = save(name, ASSETS[name], raw)
            print("        saved {} ({:.0f} KB)".format(os.path.basename(path), size / 1024), flush=True)
            ok += 1
        except Exception as exc:  # keep going; one bad asset shouldn't stop the run
            print("        FAILED: {}".format(exc)[:300], flush=True)
            failed.append(name)
        time.sleep(2)

    print("\ndone: {} ok, {} failed".format(ok, len(failed)))
    if failed:
        print("failed:", " ".join(failed))


if __name__ == "__main__":
    sys.exit(main() or 0)
