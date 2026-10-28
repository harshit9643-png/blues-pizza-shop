"""Side-view walk cycles (character sheets) with OpenAI's image model (the ChatGPT image model).

Same output as tools/gen_walk.py (assets/story/walk/<name>_0..3.webp + manifest.json), but each
character's front-view art goes to the OpenAI image-edit endpoint as the reference, so the side view
keeps its look. The key is read from a file, never from the command line:

    OPENAI_KEY_FILE=<path to a file holding the key>   (default: openai.key in the scratchpad below)
    python -I tools/gen_walk_openai.py
    python -I tools/gen_walk_openai.py monty --force
"""

import base64
import io
import json
import os
import sys
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_walk import CHARS, OUT, PROMPT, split_row  # noqa: E402
from gen_assets import ROOT, key_out  # noqa: E402

KEY_FILE = os.environ.get(
    "OPENAI_KEY_FILE",
    r"C:\Users\Lenovo\AppData\Local\Temp\claude\c--Users-Lenovo-Downloads-Billu-pizza-shop"
    r"\9cd5f55a-8dea-4359-9bd2-12c37aa50555\scratchpad\openai.key",
)
MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")


def multipart(fields, files):
    b = uuid.uuid4().hex
    out = io.BytesIO()
    for k, v in fields.items():
        out.write(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, (fn, data, ct) in files.items():
        out.write(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\nContent-Type: {ct}\r\n\r\n'.encode())
        out.write(data + b"\r\n")
    out.write(f"--{b}--\r\n".encode())
    return out.getvalue(), "multipart/form-data; boundary=" + b


def make(name, key):
    from PIL import Image
    src, desc = CHARS[name]
    ref = Image.open(os.path.join(ROOT, "assets", "web", src + ".webp")).convert("RGBA")
    buf = io.BytesIO()
    ref.save(buf, "PNG")
    body, ct = multipart({"model": MODEL, "prompt": PROMPT.format(desc=desc), "size": "1536x1024", "n": "1"},
                         {"image[]": (src + ".png", buf.getvalue(), "image/png")})
    req = urllib.request.Request("https://api.openai.com/v1/images/edits", data=body,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": ct})
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.load(resp)
    raw = base64.b64decode(data["data"][0]["b64_json"])
    im = key_out(raw, "magenta")
    im.save(os.path.join(OUT, name + "_sheet.png"))
    frames = split_row(im)
    for i, f in enumerate(frames):
        f = f.resize((round(f.width * 512 / f.height), 512))
        f.save(os.path.join(OUT, f"{name}_{i}.webp"), "WEBP", quality=90)
    return frames[0].width / frames[0].height


def main():
    args = sys.argv[1:]
    force = "--force" in args
    names = [a for a in args if a in CHARS] or list(CHARS)
    os.makedirs(OUT, exist_ok=True)
    key = open(KEY_FILE).read().strip()
    man_path = os.path.join(OUT, "manifest.json")
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    for n in names:
        if not force and os.path.exists(os.path.join(OUT, n + "_0.webp")):
            continue
        try:
            man[n] = {"frames": 4, "aspect": round(make(n, key), 4)}
            print("saved", n, flush=True)
        except urllib.error.HTTPError as e:
            print("FAILED", n, e.code, e.read()[:300], flush=True)
        except Exception as exc:
            print("FAILED", n, str(exc)[:300], flush=True)
    json.dump(man, open(man_path, "w"), indent=1)
    print("manifest:", man)


if __name__ == "__main__":
    main()
