from __future__ import annotations

from http.server import ThreadingHTTPServer

from app.config import HOST, SERVER_PORT
from app.web import BlackIceRequestHandler


if __name__ == '__main__':
    server = ThreadingHTTPServer((HOST, SERVER_PORT), BlackIceRequestHandler)
    print(f'Server app running at http://{HOST}:{SERVER_PORT}')
    server.serve_forever()