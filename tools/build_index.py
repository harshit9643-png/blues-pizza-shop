"""Build index.html, the page GitHub Pages serves, from the current game.

    python -I tools/build_index.py

The game file is written without its own <!doctype>/<head> (the artifact host and
tools/serve.py add those). index.html wraps it in the same skeleton so it plays
as a normal web page. Re-run after changing the game, then commit both files.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import GAME, ROOT, SKELETON_HEAD, SKELETON_TAIL  # noqa: E402


def main():
    with open(GAME, encoding="utf-8") as fh:
        body = fh.read()
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(SKELETON_HEAD + body + SKELETON_TAIL)
    print("index.html built from", os.path.basename(GAME), f"({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
