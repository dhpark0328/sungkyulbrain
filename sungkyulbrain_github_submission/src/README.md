# blackice_python_314_easy

전종설 발표자료 기준으로 다시 정리한 **Python 3.14 친화형** 프로토타입입니다.

핵심 목표:
1. C 압축파일은 참고만 하고, 발표자료 기준 구조로 재작성
2. 설치 충돌을 줄이기 위해 외부 패키지 없이 표준 라이브러리 중심으로 구현
3. 단말 → 게이트웨이 → 서버 → DB → 웹 지도 시각화 흐름을 유지

## 실행 방법 (Windows PowerShell)

```powershell
python integrated_app.py
```

브라우저:

```text
http://127.0.0.1:8000
```

센서 시뮬레이터:

```powershell
python scripts\run_node.py --gateway http://127.0.0.1:8000 --count 8 --mode mixed
```

## 분리 실행

서버:

```powershell
python server_app.py
```

게이트웨이:

```powershell
python gateway_app.py
```

노드:

```powershell
python scripts\run_node.py --gateway http://127.0.0.1:8001 --count 8 --mode mixed
```

## Task 매핑

- 1. 단말 노드 측정: `scripts/run_node.py`
- 2. 구조체형 전달: `app/models.py` 의 `SensorPacket`
- 3. 게이트웨이에서 서버로 전송: `gateway_app.py`
- 4. 서버 DB 저장 및 노면 판단: `app/db.py`, `app/inference.py`
- 5. 결과를 프론트로 전송: `app/web.py`
- 6. 지도 출력 및 학교 주변 노드 생성: `app/map_seed.py`, `static/app.js`
- 7. AWS 서버 분리 또는 통합: `server_app.py`, `gateway_app.py`, `integrated_app.py`

## 향후 진행 Checklist 반영

- Random Delay 반영
- payload 구조 고정
- DB 스키마 분리
- CSV export 추가
- 웹 시연 구조 유지

## 다음 단계 제안

- 실제 LoRa UART 수신 코드 연결
- KMA API 실연동
- 규칙 기반 판단을 XGBoost 모델로 교체
- AWS 배포용 리버스 프록시/도메인 정리
