"""Build the game and serve it locally, the same way it is served online.

    python3 tools/serve.py            # http://localhost:8000
    python3 tools/serve.py 8080

Runs tools/build.py first, then serves dist/ with clean addresses like Vercel:
/ is the game, /level2 is Level 2. Re-run after editing anything in src/.
"""

import http.server
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(REPO, "dist")
PORT = 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    # Windows' mimetypes table often lacks webp
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".webp": "image/webp"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST, **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        # clean addresses: /level2 serves level2.html
        if path != "/" and "." not in os.path.basename(path) and os.path.isfile(os.path.join(DIST, path.strip("/") + ".html")):
            self.path = path.rstrip("/") + ".html"
        return super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    subprocess.run([sys.executable, os.path.join(REPO, "tools", "build.py")], check=True)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler) as srv:
        print(f"Billu's Pizza Kitchen at http://localhost:{port}")
        srv.serve_forever()
