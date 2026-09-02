# 4교시. 코드 리뷰와 테스트 — 사람 눈과 기계 눈


# 리뷰 대상 코드 — 결함을 일부러 심어 둔 코드다. 돌아가지만 사고투성이다
import json

import requests

url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" # Day 8 1교시 — 설정 분리
headers = {"Authorization": "Bearer AIzaSyB-fake-key-1234"} # Day 4 — 비밀은 코드에 적지 않는다

def a(x): # Day 1 — 읽는 사람을 위한 이름
    body = {"model": "gemini-3.5-flash-lite", "messages": [{"role": "user", "content": x}]}
    try:
        r = requests.post(url, headers=headers, json=body)
        return json.loads(r.json()["choices"][0]["message"]["content"]) # Day 6~7 — LLM은 그럴듯하게 틀린다
    except Exception:
        pass # 숨은 3: 모든 예외를 처리 없이 조용히 죽음 -> None 리턴으로 호출부에서 에러 터짐

alerts = json.load(open("enriched_alerts.json", encoding="utf-8"))["alerts"] # Day 2·5·8 — 실패는 정상 상황이다
for temp in alerts:
    j = a("다음 경보를 판단해라: " + json.dumps(temp, ensure_ascii=False))
    if j["severity"] == "high" or "medium": # 숨은 1: 무조건 참
        approve = input(f"{j['tool']} 조치를 실행할까요? (y/n) ")
        if approve != "n": # 숨은 2: n만 아니면 참
            print("[조치]", j["tool"])

    # Day 6~7 — 기록이 전부다, 뼈대는 코드가

print(f"[완료] {len(alerts)}건 판단 완료")