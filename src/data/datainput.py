import os
import requests
import json
import time
from datetime import datetime

# 1. 본인의 AWS API Gateway 주소와 API 키로 반드시 변경하십시오.
API_URL = os.getenv("BLACKICE_AWS_API_URL", "")
API_KEY = os.getenv("BLACKICE_AWS_API_KEY", "")

# 2. 5개 노드에 전송할 임의의 데이터 리스트 (map_seed.py의 ID와 일치시켰습니다.)
mock_data_list = [
    # Dry (안전) 구간: 전도도 850 ~ 1000
    {"device_id": "node-1", "temperature": 5.5, "humidity": 32, "conductivity": 960, "latitude": "37.3820", "longitude": "126.9302"},
    {"device_id": "node-2", "temperature": 4.8, "humidity": 35, "conductivity": 920, "latitude": "37.3828", "longitude": "126.9281"},
    
    # Wet (주의) 구간: 전도도 0 ~ 100
    {"device_id": "node-3", "temperature": 2.1, "humidity": 89, "conductivity": 42, "latitude": "37.3798", "longitude": "126.9305"},
    
    # Frozen (위험) 구간: 전도도 100 ~ 850
    {"device_id": "node-4", "temperature": -1.8, "humidity": 68, "conductivity": 380, "latitude": "37.3801", "longitude": "126.9279"},
    {"device_id": "node-5", "temperature": -3.5, "humidity": 52, "conductivity": 710, "latitude": "37.3813", "longitude": "126.9272"}
]

def send_all_nodes_data():
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    print("AWS DynamoDB로 5개 노드 테스트 데이터 전송을 시작합니다...\n")

    for data in mock_data_list:
        # 데이터가 전송되는 시점의 현재 시간을 YYYY-MM-DD HH:MM:SS 형식으로 추가합니다.
        data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # AWS로 데이터 전송 (POST)
            response = requests.post(API_URL, data=json.dumps(data), headers=headers)
            
            if response.status_code == 200:
                print(f"[{data['device_id']}] 전송 성공 -> 전도도: {data['conductivity']}, 시간: {data['time']}")
            else:
                print(f"[{data['device_id']}] 전송 실패 (코드: {response.status_code}) -> {response.text}")
                
        except Exception as e:
            print(f"[{data['device_id']}] 에러 발생: {e}")
        
        # 각 전송 사이에 1초의 간격을 둡니다.
        time.sleep(1)

    print("\n모든 데이터 전송이 완료되었습니다. 웹 대시보드를 새로고침하여 확인해 보세요.")

if __name__ == "__main__":
    send_all_nodes_data()