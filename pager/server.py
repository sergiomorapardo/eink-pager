"""Servidor local del pager (solo stdlib + Pillow).

Entradas:
  POST /hook    JSON de un hook de Claude Code
  POST /usage   objeto `rate_limits` del statusline
  POST /digest  resumen de correo/agenda (ver pager/digest.py)
Salidas:
  GET /         simulador web (se refresca solo)
  GET /frame.png  imagen para el simulador
  GET /frame.bmp  1 bit, para el firmware del ESP32
  GET /state.json estado crudo, para depurar
"""

from __future__ import annotations

import argparse
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .render import render
from .state import State

SIMULATOR = """<!doctype html><meta charset=utf-8><title>E ink pager</title>
<style>body{background:#ddd;display:grid;place-items:center;height:100vh;margin:0;font:13px system-ui}
img{image-rendering:pixelated;width:888px;border:14px solid #222;border-radius:10px;background:#fff}</style>
<div><img id=f src=/frame.png><p>Simulador · refresco cada 10 s</p></div>
<script>setInterval(()=>f.src='/frame.png?'+Date.now(),10000)</script>"""


def make_handler(state: State):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # silencioso: los hooks pegan seguido
            pass

        def _send(self, body: bytes, ctype: str, code: int = 200):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/":
                self._send(SIMULATOR.encode(), "text/html; charset=utf-8")
            elif path in ("/frame.png", "/frame.bmp"):
                buf = io.BytesIO()
                render(state).save(buf, "PNG" if path.endswith("png") else "BMP")
                self._send(buf.getvalue(), "image/png" if path.endswith("png") else "image/bmp")
            elif path == "/state.json":
                self._send(json.dumps(state.data, ensure_ascii=False).encode(), "application/json")
            else:
                self._send(b"not found", "text/plain", 404)

        def do_POST(self):
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n) or b"{}")
            except (ValueError, json.JSONDecodeError):
                return self._send(b"bad json", "text/plain", 400)
            if self.path == "/hook":
                state.apply_hook(payload)
            elif self.path == "/usage":
                state.set_usage(payload)
            elif self.path == "/digest":
                state.set_digest(payload)
            else:
                return self._send(b"not found", "text/plain", 404)
            self._send(b"ok", "text/plain")

    return Handler


def main():
    ap = argparse.ArgumentParser(description="Servidor local del E ink pager")
    ap.add_argument("--host", default="127.0.0.1", help="usa 0.0.0.0 cuando el ESP32 deba alcanzarlo")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(State()))
    print(f"Pager en http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
