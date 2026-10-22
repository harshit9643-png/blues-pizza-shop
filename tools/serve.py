"""Serve the game locally at http://localhost:8000

The game file is written for the artifact host, which wraps it in a document
skeleton (doctype, charset, viewport, a small reset). This server adds the same
skeleton on the fly, so the local page renders exactly like the published one,
and always serves the latest saved version of the game.

    python -I tools/serve.py            # port 8000
    python -I tools/serve.py 8080
"""

import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "level1_draft2.html")      # the current game opens at /
PORT = 8000

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


class Handler(http.server.SimpleHTTPRequestHandler):
    # Windows' mimetypes table often lacks webp
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".webp": "image/webp"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        page = GAME if path in ("/", "/index.html") else os.path.join(ROOT, path.lstrip("/"))
        # any top-level game page written for the artifact host gets the skeleton
        if page.endswith(".html") and os.path.dirname(os.path.abspath(page)) == ROOT and os.path.isfile(page):
            with open(page, encoding="utf-8") as fh:
                body = (SKELETON_HEAD + fh.read() + SKELETON_TAIL).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def end_headers(self):
        # always fresh while iterating on art and code
        if not self.path.split("?", 1)[0].endswith((".html", "/")):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler) as srv:
        print("Blue's Pizza Shop running at http://localhost:{}".format(port), flush=True)
        srv.serve_forever()
