from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

from app.config import GATEWAY_PORT, HOST, SERVER_URL


class GatewayHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != '/api/gateway/ingest':
            self._send_json({'error': 'not found'}, status=404)
            return
        length = int(self.headers.get('Content-Length', '0'))
        payload = self.rfile.read(length)
        try:
            req = Request(
                f'{SERVER_URL}/api/server/ingest',
                data=payload,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                method='POST',
            )
            with urlopen(req, timeout=10) as response:
                body = response.read().decode('utf-8')
                self._send_json(json.loads(body), status=response.status)
        except Exception as exc:
            self._send_json({'error': 'forward failed', 'detail': str(exc)}, status=502)

    def log_message(self, format: str, *args) -> None:
        return


if __name__ == '__main__':
    server = ThreadingHTTPServer((HOST, GATEWAY_PORT), GatewayHandler)
    print(f'Gateway app running at http://{HOST}:{GATEWAY_PORT}')
    server.serve_forever()
