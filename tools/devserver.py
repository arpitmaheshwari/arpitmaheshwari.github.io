#!/usr/bin/env python3
"""Local preview server that REFUSES to be cached.

Why this exists: python -m http.server sends no cache headers, so browsers
happily reuse an old index.html. Three review rounds were spent on "the fix
didn't work" when the fix was on disk and the browser was showing yesterday.
Every response here carries no-store, so what you see is always what is saved.
"""
import sys, os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    def log_message(self, fmt, *args):
        pass  # quiet: the preview pane shows failures, not every 200

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    root = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    os.chdir(root)
    print(f"serving {root} on :{port} with no-store (nothing here will be cached)")
    ThreadingHTTPServer(('', port), NoCache).serve_forever()
