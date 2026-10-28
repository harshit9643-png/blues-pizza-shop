"""Package the whole game (story, tutorials, Level 1.1, 1.2 and Level 2) into one self-contained folder.

    python -I tools/package_game.py

Writes Final/ in this project (the online link serves it too):
    index.html            main screen (PLAY), story, tutorial, Level 1.1 and 1.2
    level2/index.html     Level 2
    assets/               only the art the two pages load
Open index.html by double-clicking, or host the folder anywhere.
"""

import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import ROOT, SKELETON_HEAD, SKELETON_TAIL  # noqa: E402

NAME = "Final"
PAGES = {"index.html": ("level1_draft2.html", ""), "level2/index.html": ("level2.html", "../")}


def wrap(src, base):
    with open(os.path.join(ROOT, src), encoding="utf-8") as fh:
        body = fh.read()
    head = SKELETON_HEAD.replace("<head>\n", f'<head>\n<base href="{base}">\n', 1) if base else SKELETON_HEAD
    return head + body + SKELETON_TAIL, body


def main():
    out = os.path.join(ROOT, NAME)
    if os.path.exists(out):
        shutil.rmtree(out)
    used = set()
    for rel, (src, base) in PAGES.items():
        page, body = wrap(src, base)
        dest = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page)
        used |= set(re.findall(r"assets/[A-Za-z0-9_/\-]+\.(?:webp|svg|png|jpg)", body))
    # the pages also build file names in code (characters, topping pieces, pizzas): ship those folders whole
    folders = ["assets/web", "assets/web/hd", "assets/web/noori_anim", "assets/draft2"]
    files = set(used)
    for f in folders:
        for fn in os.listdir(os.path.join(ROOT, f)):
            if fn.endswith(".webp"):
                files.add(f"{f}/{fn}")
    missing = []
    for rel in sorted(files):
        s = os.path.join(ROOT, rel)
        if not os.path.isfile(s):
            missing.append(rel)
            continue
        d = os.path.join(out, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(s, d)
    with open(os.path.join(out, "README.txt"), "w", encoding="utf-8") as fh:
        fh.write("Billu's Pizza Kitchen - fractions game (story, tutorials, Level 1.1, Level 1.2, Level 2)\n\n"
                 "Double-click index.html to play. Chrome or Edge recommended.\n"
                 "Press PLAY: the story, the tutorial, Level 1.1, 1.2, then Level 2. The menu at the top jumps anywhere.\n"
                 "Fonts come from Google Fonts, so an internet connection gives the intended look.\n")
    total = sum(os.path.getsize(os.path.join(b, f)) for b, _, fs in os.walk(out) for f in fs)
    print(f"{NAME}/  {len(files) - len(missing) + len(PAGES) + 1} files, {total / 1048576:.1f} MB")
    if missing:
        print("MISSING:", ", ".join(missing))
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
