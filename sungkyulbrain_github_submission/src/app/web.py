from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from .bootstrap import bootstrap
from .config import BASE_DIR, SCHOOL_LAT, SCHOOL_LON, SCHOOL_NAME, STATIC_DIR, AWS_API_URL, AWS_API_KEY
from .inference import infer_road_state
from .map_seed import default_nodes  # DB 대신 하드코딩된 노드 리스트를 직접 가져옵니다.
from .db import export_readings_csv, store_packet
from .models import SensorPacket, utc_now

#bootstrap()

class BlackIceRequestHandler(BaseHTTPRequestHandler):
    server_version = 'BlackIceHTTP/1.0'

    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, content_type: str = 'text/plain; charset=utf-8', status: int = 200) -> None:
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length) if length else b'{}'
        return json.loads(raw.decode('utf-8'))

    def _serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._send_text('Not Found', status=404)
            return
        content = path.read_bytes()
        mime, _ = mimetypes.guess_type(path.name)
        self.send_response(200)
        self.send_header('Content-Type', mime or 'application/octet-stream')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-api-key')
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            html = (STATIC_DIR / 'index.html').read_text(encoding='utf-8')
            html = html.replace('__SCHOOL_NAME__', SCHOOL_NAME)
            html = html.replace('__SCHOOL_LAT__', str(SCHOOL_LAT))
            html = html.replace('__SCHOOL_LON__', str(SCHOOL_LON))
            self._send_text(html, content_type='text/html; charset=utf-8')
            return
            
        if parsed.path.startswith('/static/'):
            rel = parsed.path.replace('/static/', '', 1)
            self._serve_file(STATIC_DIR / rel)
            return

        if parsed.path == '/api/health':
            self._send_json({'status': 'ok', 'time': utc_now()})
            return

        # 1. 전체 노드 맵 데이터 (map_seed.py 위치 + AWS 센서 결합)
        if parsed.path == '/api/map/nodes':
            try:
                # DB 조회 대신 map_seed.py의 파이썬 리스트를 그대로 사용합니다.
                local_devices = default_nodes()

                req = Request(AWS_API_URL, method='GET', headers={'x-api-key': AWS_API_KEY})
                with urlopen(req, timeout=10) as response:
                    aws_data = json.loads(response.read().decode('utf-8'))

                latest_nodes = {}
                for item in aws_data:
                    did = str(item.get('device_id', 'unknown'))
                    t_str = item.get('time', '')
                    if did not in latest_nodes or t_str > latest_nodes[did].get('time', ''):
                        latest_nodes[did] = item

                nodes = []
                for d in local_devices:
                    did = str(d['device_id'])
                    aws_item = latest_nodes.get(did)

                    if aws_item:
                        t = float(aws_item.get('temperature', 0))
                        h = float(aws_item.get('humidity', 0))
                        c = float(aws_item.get('conductivity', 0))
                        measured_at = aws_item.get('time', '')
                        status, risk_score, reason = infer_road_state(t, h, c)
                    else:
                        t = h = c = 0
                        measured_at = '데이터 없음'
                        status, risk_score, reason = 'unknown', 0, '데이터 없음'

                    nodes.append({
                        'device_id': did,
                        'latitude': float(d['latitude']),
                        'longitude': float(d['longitude']),
                        'name': d.get('name', f"Node {did}"),
                        'measured_at': measured_at,
                        'temperature_c': t,
                        'humidity_pct': h,
                        'conductivity': c,      
                        'frequency_hz': c,      
                        'road_status': status,
                        'risk_score': risk_score,
                        'reason': reason
                    })

                self._send_json({
                    'school': {'name': SCHOOL_NAME, 'latitude': SCHOOL_LAT, 'longitude': SCHOOL_LON},
                    'nodes': nodes
                })
            except Exception as e:
                print("AWS Fetch Error:", e)
                self._send_json({'error': 'Failed to fetch from AWS', 'detail': str(e)}, status=502)
            return

        # 2. 개별 노드 상세 데이터 (map_seed.py 단일 위치 + AWS 센서 결합)
        if parsed.path.startswith('/api/map/node/'):
            device_id = parsed.path.rsplit('/', 1)[-1]
            try:
                # DB 대신 map_seed.py 리스트에서 해당 디바이스 ID를 검색합니다.
                local_devices = default_nodes()
                target_device = None
                for d in local_devices:
                    if str(d['device_id']) == str(device_id):
                        target_device = d
                        break

                if not target_device:
                    self._send_json({'error': 'node not found in map_seed.py'}, status=404)
                    return

                req = Request(AWS_API_URL, method='GET', headers={'x-api-key': AWS_API_KEY})
                with urlopen(req, timeout=10) as response:
                    aws_data = json.loads(response.read().decode('utf-8'))
                
                target_item = None
                for item in aws_data:
                    if str(item.get('device_id')) == str(device_id):
                        if target_item is None or item.get('time', '') > target_item.get('time', ''):
                            target_item = item
                
                if target_item:
                    t = float(target_item.get('temperature', 0))
                    h = float(target_item.get('humidity', 0))
                    c = float(target_item.get('conductivity', 0))
                    measured_at = target_item.get('time', '')
                    status, risk_score, reason = infer_road_state(t, h, c)
                else:
                    t = h = c = 0
                    measured_at = '데이터 없음'
                    status, risk_score, reason = 'unknown', 0, '데이터 없음'
                    
                self._send_json({
                    'device_id': str(target_device['device_id']),
                    'latitude': float(target_device['latitude']),
                    'longitude': float(target_device['longitude']),
                    'name': target_device.get('name', f"Node {target_device['device_id']}"),
                    'measured_at': measured_at,
                    'temperature_c': t,
                    'humidity_pct': h,
                    'conductivity': c,
                    'frequency_hz': c,
                    'road_status': status,
                    'risk_score': risk_score,
                    'reason': reason
                })
            except Exception as e:
                self._send_json({'error': 'AWS fetch failed', 'detail': str(e)}, status=502)
            return

        # 3. 우측 하단 최근 목록 데이터
        if parsed.path == '/api/readings/recent':
            query = parse_qs(parsed.query)
            limit = int(query.get('limit', ['20'])[0])
            try:
                req = Request(AWS_API_URL, method='GET', headers={'x-api-key': AWS_API_KEY})
                with urlopen(req, timeout=10) as response:
                    aws_data = json.loads(response.read().decode('utf-8'))
                
                aws_data.sort(key=lambda x: x.get('time', ''), reverse=True)
                
                items = []
                for item in aws_data[:limit]:
                    t = float(item.get('temperature', 0))
                    h = float(item.get('humidity', 0))
                    c = float(item.get('conductivity', 0))
                    status, risk_score, reason = infer_road_state(t, h, c)
                    
                    items.append({
                        'device_id': str(item.get('device_id', 'unknown')),
                        'measured_at': item.get('time', ''),
                        'temperature_c': t,
                        'humidity_pct': h,
                        'conductivity': c,
                        'frequency_hz': c,
                        'road_status': status,
                        'risk_score': risk_score
                    })
                self._send_json({'items': items})
            except Exception as e:
                self._send_json({'error': 'AWS fetch failed', 'detail': str(e)}, status=502)
            return

        self._send_text('Not Found', status=404)

    def do_POST(self) -> None:
        self._send_json({'error': 'not implemented'}, status=404)

    def log_message(self, format: str, *args) -> None:
        return