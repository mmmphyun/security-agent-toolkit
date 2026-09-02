# 2교시. 알림 연동 — 실패해도 멈추지 않게

import json
import os
import requests

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = "config.json"
CONFIG_PATH = os.path.join(BASE_DIR,  CONFIG_FILE)
FILE_PATH = os.path.join(BASE_DIR, "reports", "test.md")

with open(CONFIG_PATH, encoding="utf-8") as f:   # 설정 파일을 읽는다 (1교시)
    config = json.load(f)

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", config.get("webhook_url"))

def make_message(count, filename):
    return f"[관제 데스크] 판단 {count}건 처리 완료 — 보고서: {filename}"

def notify(filename):
    try:
        requests.post(config["webhook_url"], json={"rule": "daily_report", "file": filename})
        print("[알림] 웹훅 전송 완료")
    except requests.exceptions.ConnectionError:
        print("[알림 실패] 웹훅 - 서버가 꺼져 있다, 계속 간다")

    try:
        message = make_message(3, filename)
        response = requests.post(WEBHOOK_URL, json={"text": message})
        print("[알림] Slack 전송 완료")
    except requests.exceptions.ConnectionError:
        print("[알림 실패] Slack — 주소에 닿지 못했다, 계속 간다")


    print("(notify 끝)")

notify(FILE_PATH)
print("[파이프라인 완료] 알림과 무관하게 여기까지 온다")