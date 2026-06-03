from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

NODES = [
    ('node-a1', 37.3811, 126.9293),
    ('node-a2', 37.3820, 126.9271),
    ('node-a3', 37.3787, 126.9297),
    ('node-a4', 37.3791, 126.9268),
    ('node-a5', 37.3804, 126.9261),
    ('node-a6', 37.3823, 126.9284),
]


def measurement_for_mode(mode: str) -> tuple[float, float, float]:
    if mode == 'ice':
        return random.uniform(950, 1120), random.uniform(-4.0, 0.5), random.uniform(82, 96)
    if mode == 'wet':
        return random.uniform(1180, 1340), random.uniform(0.0, 4.0), random.uniform(70, 90)
    return random.uniform(1380, 1650), random.uniform(2.0, 10.0), random.uniform(35, 70)


def post_json(url: str, payload: dict) -> tuple[int, str]:
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = Request(url, data=data, headers={'Content-Type': 'application/json; charset=utf-8'}, method='POST')
    with urlopen(req, timeout=10) as response:
        return response.status, response.read().decode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate roadside nodes')
    parser.add_argument('--gateway', default='http://127.0.0.1:8000', help='Gateway base URL')
    parser.add_argument('--count', type=int, default=6, help='Number of packets to send')
    parser.add_argument('--mode', choices=['mixed', 'dry', 'wet', 'ice'], default='mixed')
    args = parser.parse_args()

    for seq in range(1, args.count + 1):
        node = NODES[(seq - 1) % len(NODES)]
        mode = args.mode if args.mode != 'mixed' else random.choice(['dry', 'wet', 'ice'])
        frequency_hz, temperature_c, humidity_pct = measurement_for_mode(mode)
        random_delay_ms = random.randint(100, 1500)
        time.sleep(random_delay_ms / 1000)
        payload = {
            'schema_version': 1,
            'device_id': node[0],
            'gateway_id': 'gateway-1',
            'sequence_no': seq,
            'measured_at': datetime.now(timezone.utc).isoformat(),
            'battery_v': round(random.uniform(3.55, 4.18), 2),
            'random_delay_ms': random_delay_ms,
            'latitude': node[1],
            'longitude': node[2],
            'measurement': {
                'frequency_hz': round(frequency_hz, 2),
                'temperature_c': round(temperature_c, 2),
                'humidity_pct': round(humidity_pct, 2),
            },
        }
        status, body = post_json(f"{args.gateway.rstrip('/')}/api/gateway/ingest", payload)
        print(f'[{seq}] mode={mode} status={status} body={body}')
