"""Build the deployable site from the game source.

    python3 tools/build.py

Reads  src/level1.html, src/level2.html and src/assets/
Writes dist/
    index.html     main screen (PLAY), Story 1, Tutorial 1.1, Levels 1.1 and 1.2   ->  /
    level2.html    Story 2, Tutorial 2, the matches, the Final and the Champion    ->  /level2
    assets/        only the art the two pages load
    404.html       sends any unknown address back to the game

The source pages are page bodies (no <html>/<head>); the build wraps each one in a full
HTML document. Vercel runs this script on every deploy (see vercel.json). dist/ is a
build output and is not committed.
"""

import hashlib
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")
OUT = os.path.join(REPO, "dist")

SITE = "Billu's Pizza Kitchen"
DESCRIPTION = ("A fractions game for classes 6 and 7: help Chef Billu cut, top and serve pizza "
               "slices, then judge the Big Eater Contest.")

# output page -> (source page, title)
PAGES = {
    "index.html": ("level1.html", SITE),
    "level2.html": ("level2.html", f"{SITE} · Big Eater Contest"),
}

# the pages also build file names in code (characters, toppings, pizzas): ship these folders whole
WHOLE_FOLDERS = ["assets/web", "assets/web/hd", "assets/web/noori_anim", "assets/draft2", "assets/ui", "assets/story", "assets/prelbd"]
ASSET_RE = re.compile(r"assets/[A-Za-z0-9_/\-]+\.(?:webp|svg|png|jpg)")

FAVICON = ("data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Cpath d='M32 6 58 54Q32 64 6 54Z' fill='%23F6C34A' stroke='%23B97410' stroke-width='4' stroke-linejoin='round'/%3E"
           "%3Ccircle cx='32' cy='30' r='5' fill='%23D2402E'/%3E%3Ccircle cx='24' cy='46' r='5' fill='%23D2402E'/%3E"
           "%3Ccircle cx='41' cy='47' r='5' fill='%23D2402E'/%3E%3C/svg%3E")

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#2B2546">
<meta property="og:title" content="{site}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<link rel="icon" href="{favicon}">
<style>
:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px system-ui,-apple-system,sans-serif}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
</style>
</head>
<body>
"""
TAIL = "\n</body>\n</html>\n"

NOT_FOUND = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{site}</title>
<meta http-equiv="refresh" content="0; url=/"><link rel="icon" href="{favicon}"></head>
<body><a href="/">Play {site}</a></body></html>
"""


def page_html(src_name, title):
    with open(os.path.join(SRC, src_name), encoding="utf-8") as fh:
        body = fh.read()
    # title and host-only meta tags belong in the head the build writes
    body = re.sub(r"<title>.*?</title>\s*", "", body, count=1, flags=re.S)
    body = re.sub(r'<meta name="claude:[^"]*"[^>]*>\s*', "", body)
    # <link> tags go into the head; web fonts load without holding up the page (text shows at once, then swaps)
    links = re.findall(r"<link [^>]*>", body)
    body = re.sub(r"<link [^>]*>\s*", "", body)
    extra = ['<link rel="preconnect" href="https://fonts.googleapis.com">']
    for tag in links:
        if 'rel="stylesheet"' in tag and "fonts.googleapis.com" in tag:
            href = re.search(r'href="([^"]+)"', tag).group(1)
            extra.append(f'<link rel="preload" as="style" href="{href}">')
            extra.append(f'<link rel="stylesheet" href="{href}" media="print" onload="this.media=\'all\'">')
            extra.append(f'<noscript><link rel="stylesheet" href="{href}"></noscript>')
        else:
            extra.append(tag)
    head = HEAD.format(title=title, site=SITE, description=DESCRIPTION, favicon=FAVICON)
    head = head.replace("<style>", "\n".join(extra) + "\n<style>", 1)
    return head + versioned(body) + TAIL, body


def versioned(body):
    """Give every art link a ?v=<content hash>, so a changed picture is fetched again, not taken from the browser cache."""
    def tag(m):
        path = os.path.join(SRC, m.group(0))
        if not os.path.isfile(path):
            return m.group(0)
        with open(path, "rb") as fh:
            return m.group(0) + "?v=" + hashlib.sha1(fh.read()).hexdigest()[:8]
    body = ASSET_RE.sub(tag, body)
    # pictures whose names are put together in code carry the build's stamp instead
    stamp = hashlib.sha1(body.encode("utf-8")).hexdigest()[:8]
    return body.replace("__BUILD__", stamp)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    used = set()
    for out_name, (src_name, title) in PAGES.items():
        html, body = page_html(src_name, title)
        with open(os.path.join(OUT, out_name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        used |= set(ASSET_RE.findall(body))
    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(NOT_FOUND.format(site=SITE, favicon=FAVICON))

    files = set(used)
    for folder in WHOLE_FOLDERS:
        for fn in os.listdir(os.path.join(SRC, folder)):
            if fn.endswith(".webp"):
                files.add(f"{folder}/{fn}")
    # the background music (tools/make_bgm.py)
    au = os.path.join(SRC, "assets", "audio")
    if os.path.isdir(au):
        files |= {f"assets/audio/{fn}" for fn in os.listdir(au) if fn.endswith(".mp3")}
    # the AI voice clips and their list (tools/voices.py)
    vo = os.path.join(SRC, "assets", "vo")
    if os.path.isdir(vo):
        for fn in os.listdir(vo):
            if fn.endswith(".mp3") or fn == "manifest.json":
                files.add(f"assets/vo/{fn}")
    missing = []
    for rel in sorted(files):
        src = os.path.join(SRC, rel)
        if not os.path.isfile(src):
            missing.append(rel)
            continue
        dest = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)

    total = sum(os.path.getsize(os.path.join(b, f)) for b, _, fs in os.walk(OUT) for f in fs)
    count = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"dist/  {count} files, {total / 1048576:.1f} MB")
    if missing:
        print("MISSING:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
