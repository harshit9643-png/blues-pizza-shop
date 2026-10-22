"""Build a play page for GitHub Pages from the current game.

    python -I tools/build_index.py          # index.html (the main play link)
    python -I tools/build_index.py v2       # v2/index.html, its own link; the main one is untouched

The game file is written without its own <!doctype>/<head> (the artifact host and
tools/serve.py add those). The play page wraps it in the same skeleton so it plays
as a normal web page. A version folder gets <base href="../"> so it shares the
repository's assets instead of copying them. Re-run after changing the game, then commit.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serve import GAME, ROOT, SKELETON_HEAD, SKELETON_TAIL  # noqa: E402


def main():
    folder = sys.argv[1].strip("/\\") if len(sys.argv) > 1 else ""
    with open(GAME, encoding="utf-8") as fh:
        body = fh.read()
    head = SKELETON_HEAD
    if folder:
        depth = len(folder.replace("\\", "/").split("/"))
        head = head.replace("<head>\n", '<head>\n<base href="' + "../" * depth + '">\n', 1)
        os.makedirs(os.path.join(ROOT, folder), exist_ok=True)
    out = os.path.join(ROOT, folder, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(head + body + SKELETON_TAIL)
    print(os.path.relpath(out, ROOT), "built from", os.path.basename(GAME), f"({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
