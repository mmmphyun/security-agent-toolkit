# 2교시. 알림 연동 — 실패해도 멈추지 않게

import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = "config.json"
FILE_PATH = os.path.join(BASE_DIR,  CONFIG_FILE)

with open(FILE_PATH, encoding="utf-8") as f:   # 설정 파일을 읽는다 (1교시)
    config = json.load(f)

message = "[관제 데스크] 판단 3건 처리 완료 — 보고서: reports/2026-09/daily_report_2026-09-01.md"

'''
강의 자료에서는 config.json에 webhook 링크를 넣으라 했으나, 보안상 토큰 노출 위험 및 환경 격리를 위해 .env에 넣고 불러옴.
'''
webhook_url = os.environ.get("SLACK_WEBHOOK_URL", config.get("webhook_url"))

response = requests.post(webhook_url, json={"text": message})   # Slack은 {"text": ...} 모양을 원한다
print("응답 코드:", response.status_code)
print("응답 내용:", response.text)