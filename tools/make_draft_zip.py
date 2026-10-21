"""Freeze a game page and its art into a self-contained draft folder + ZIP.

    python -I tools/make_draft_zip.py <game.html> <draft-name>

Creates drafts/<draft-name>/ (index.html + only the assets the page uses + README)
and drafts/<draft-name>.zip. The page is wrapped in the same document skeleton the
artifact host adds, so it opens correctly by double-clicking index.html.
"""

import os
import re
import shutil
import sys
import zipfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKELETON_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font:14px system-ui,-apple-system,sans-serif}
img{max-width:100%}
[hidden]{display:none!important}
</style>
</head>
<body>
"""
SKELETON_TAIL = "\n</body>\n</html>\n"

CUSTOMERS = ["tez", "monty", "ant", "squirrel", "bijli", "badal", "madhu", "peacock", "jhumru",
             "frog", "gorilla", "mouse", "croc", "rabbit", "bear", "sloth", "hippo"]
TOPPINGS = ["tomato", "mushroom", "corn", "onion"]
HD_ART = ["pizza_round", "pizza_square", "pizza_rect", "pizza_cutter",
          "mould_round", "mould_square", "mould_rect"]


def assets_for(html):
    """Every asset the page loads: literal paths plus the ones it builds by name."""
    found = set(re.findall(r'assets/[A-Za-z0-9_/\-]+\.(?:webp|svg|png|jpg)', html))
    found |= {f"assets/web/{c}.webp" for c in CUSTOMERS}
    found |= {f"assets/web/piece_{t}.webp" for t in TOPPINGS}
    if "top_${" in html or "top_" in html and "assets/web/top_" in html:
        found |= {f"assets/web/top_{t}.webp" for t in TOPPINGS}
    found |= {f"assets/web/{n}.webp" for n in ("billu_happy", "noori_point")}
    found |= {f"assets/web/hd/{n}.webp" for n in HD_ART}
    if "board_empty" in html:
        found.add("assets/web/hd/board_empty.webp")
    return sorted(found)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    src, name = sys.argv[1], sys.argv[2]
    html = open(os.path.join(ROOT, src), encoding="utf-8").read()
    out = os.path.join(ROOT, "drafts", name)
    if os.path.exists(out):
        print(f"{out} already exists — pick a new draft name so nothing is overwritten")
        return 1
    os.makedirs(out)

    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(SKELETON_HEAD + html + SKELETON_TAIL)
    shutil.copy(os.path.join(ROOT, src), os.path.join(out, "source_" + os.path.basename(src)))

    missing, total = [], 0
    for rel in assets_for(html):
        s = os.path.join(ROOT, rel)
        if not os.path.isfile(s):
            missing.append(rel)
            continue
        d = os.path.join(out, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(s, d)
        total += os.path.getsize(s)

    with open(os.path.join(out, "README.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"""Billu's Pizza Shop - Level 1 - {name.replace('_', ' ')}
Saved: {date.today().isoformat()}  (from {os.path.basename(src)})

HOW TO OPEN
  Double-click index.html. Chrome or Edge recommended.
  Fonts load from Google Fonts, so an internet connection gives the intended look;
  without one the game still works with fallback fonts.

WHAT'S INSIDE
  index.html                 the game, ready to open
  source_{os.path.basename(src):<15} the same game without the page wrapper (for editing / republishing)
  assets/                    only the art this version uses

This is a frozen snapshot. Later changes are made in the working copy, not here.
""")

    zpath = os.path.join(ROOT, "drafts", name + ".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(out):
            for f in files:
                full = os.path.join(base, f)
                z.write(full, os.path.join(name, os.path.relpath(full, out)))

    print(f"folder : drafts/{name}/")
    print(f"zip    : drafts/{name}.zip  ({os.path.getsize(zpath)/1024:.0f} KB, {total/1024:.0f} KB of art)")
    print(f"assets : {len(assets_for(html)) - len(missing)} files")
    if missing:
        print("MISSING:", ", ".join(missing))
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
