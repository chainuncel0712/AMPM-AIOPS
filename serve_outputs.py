"""簡易檔案伺服器 — UTF-8 繁中友善"""
import http.server
import os
import socket

PORT = 80
DIR = "/home/pop5057273712_gmail_com/AMPM-AIOPS/outputs"

class UTF8Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        # Markdown files get utf-8 charset
        if self.path.endswith('.md') or self.path.endswith('.txt'):
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
        elif self.path.endswith('.html'):
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        elif self.path.endswith('.json'):
            self.send_header('Content-Type', 'application/json; charset=utf-8')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # quiet

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('0.0.0.0', PORT))
s.close()

print(f"🌐 檔案伺服器: http://0.0.0.0:{PORT}")
http.server.HTTPServer(('0.0.0.0', PORT), UTF8Handler).serve_forever()
