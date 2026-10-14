import json
import os
import sys
import time
import requests
from db import connect_db
from learning.support import last_event_id


def get_general_base_url():
    candidates = [
        os.environ.get("GENERAL_URL", "").rstrip("/"),
        "http://general-gateway:80",
        "http://general-api:5000",
        "http://localhost:8081",
        "http://localhost:5000",
    ]
    for url in candidates:
        if not url:
            continue
        try:
            res = requests.get(f"{url}/health", timeout=1)
            if res.status_code == 200:
                return url
        except requests.RequestException:
            continue
    return "http://general-gateway:80"


def send_requests(base_url, count):
    session = requests.Session()
    for _ in range(count):
        try:
            session.get(f"{base_url}/", timeout=3)
        except requests.RequestException:
            pass
        time.sleep(0.05)
    # 없는 경로 1회 요청 (404 발생)
    try:
        session.get(f"{base_url}/training-missing", timeout=3)
    except requests.RequestException:
        pass


def capture_events_after(after_id):
    with connect_db() as conn:
        rows = conn.execute(
            """SELECT id, method, path, status_code, event_type, occurred_at
               FROM http_events
               WHERE id > %s
               ORDER BY id ASC""",
            (after_id,),
        ).fetchall()
    for row in rows:
        row["occurred_at"] = row["occurred_at"].isoformat()
    return rows


def main():
    count = 4
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            count = 4

    # 요청 전 마지막 감시 DB ID 확인
    after_id = last_event_id()

    # 일반 서비스에 실제 요청 발생
    base_url = get_general_base_url()
    send_requests(base_url, count)

    # 비동기 전송 및 DB 저장 대기
    time.sleep(0.5)

    # 이번 요청으로 저장된 행 읽기
    events = capture_events_after(after_id)

    # 결과를 JSON 형식으로 표준 출력에 출력 (stdout 리다이렉션으로 저장 가능)
    print(json.dumps(events, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
