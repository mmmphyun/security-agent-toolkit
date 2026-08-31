import json
import os

import requests
from dotenv import load_dotenv

'''
Q. 터미널 실행 위치로 인한 logs/enriched_alerts.json 경로 깨짐 문제
A. __file__ 기반의 절대 경로 계산 방식 사용
'''
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
READ_TARGET_FILE = LOGS_DIR / "enriched_alerts.json"
SAVE_TARGET_FILE = LOGS_DIR / "agent_result.json"

# 1) 연결 준비 — 1교시
load_dotenv()                    # .env 파일을 읽어 온다 (Day 4)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"   # LLM 서비스의 창구 주소
headers = {"Authorization": "Bearer " + os.getenv("GEMINI_API_KEY"), "Content-Type": "application/json"}   # 통행증(키)을 싣는 자리

# 2) 판단 설계도 — 3교시의 severity·summary에 4교시의 tool enum을 합쳤다
JUDGMENT_FORMAT = {
    "type": "json_schema",              # 설계도 방식으로 강제한다
    "json_schema": {
        "name": "judgment",                 # 설계도 이름 (아무거나)
        "schema": {
            "type": "object",               # 답은 딕셔너리 모양
            "properties": {                 # 가질 키들
                "severity": {"type": "string", "enum": ["high", "medium", "low"]},   # 세 값 중 하나만
                "summary": {"type": "string"},                                       # 판단 근거 한 문장
                "tool": {"type": "string", "enum": ["lock_account", "block_ip", "watch"]},   # 이 세 이름 밖은 못 나온다
            },
            "required": ["severity", "summary", "tool"],   # 셋 다 필수
        },
    },
}

# 3) LLM 호출과 방어 파서 — 3교시
def ask_llm(prompt):
    body = {
        "model": "gemini-3.5-flash-lite",
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다. 항상 한국어로 답한다."},   # 2교시 — 역할과 답변 언어를 못박는다
            {"role": "user", "content": prompt},
        ],
        "response_format": JUDGMENT_FORMAT,   # 설계도를 요청에 싣는다
    }
    response = requests.post(url, headers=headers, json=body)   # 요청을 보내고 응답을 받는다
    return response.json()["choices"][0]["message"]["content"]  # 응답에서 답 문장만 돌려준다

def parse_judgment(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("[파싱 실패] JSON이 아니다:", text[:40])
        return None

# 4) 도구 상자 — 4교시
def lock_account(alert):
    print(f"[조치] 계정 잠금: {alert['user']}")
    return "locked"

def block_ip(alert):
    print(f"[조치] IP 차단: {alert['ip']}")
    return "blocked"

def watch(alert):
    print(f"[조치] 관찰 대상 등록: {alert['rule']}")
    return "watching"

tools = {"lock_account": lock_account, "block_ip": block_ip, "watch": watch}

# 5) 경보 읽기 — Day 3
def read_log_json(file_path):
    with open(file_path, encoding="utf-8") as f:
        report = json.load(f)

    if report:
        return report
    return {}

def save_result(result, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

# 6) 경보마다: 판단 → 검문 → 실행 — 검문 두 개는 5교시 도전 그대로다
def main():
    report = read_log_json(READ_TARGET_FILE)

    results = []

    for alert in report["alerts"]:
        prompt = "다음 보안 경보를 판단해라.\n경보: " + json.dumps(alert, ensure_ascii=False) + """
                쓸 수 있는 도구 목록:
                - lock_account: 계정이 공격받고 있을 때 그 계정을 잠근다
                - block_ip: 특정 IP가 공격을 보낼 때 그 IP를 차단한다
                - watch: 확실하지 않을 때 관찰 대상으로만 등록한다"""

        answer = ask_llm(prompt)
        judgment = parse_judgment(answer)   # 글자를 딕셔너리로 — 실패하면 None
        if judgment is None:
            continue

        print(f"[판단] {alert['rule']} → {judgment['severity']} — {judgment['summary']}")

        name = judgment["tool"]
        if name not in tools:                                # 검문 1 — 허용 목록 (5교시)
            judgment["result"] = "rejected"
            results.append(judgment)
            print(f"[거부] {name} — 허용 목록에 없는 도구")
            continue
        if judgment["severity"] == "high":                   # 검문 2 — 승인 게이트 (5교시)
            approve = input(f"{name} 조치를 실행할까요? (y/n) ")   # 근거는 [판단] 줄에 이미 보였다
            if approve != "y":
                judgment["result"] = "held"
                results.append(judgment)
                print(f"[보류] {alert['rule']} — 담당자가 승인하지 않음")
                continue
        judgment["result"] = tools[name](alert)              # 통과 — 같은 반복 안이니 alert를 바로 넘긴다
        results.append(judgment)

    # 기록 확인 — 건마다 무슨 조치가 어떻게 끝났는지 (5교시 과제 4 그대로)
    for r in results:
        print(f"{r['tool']}: {r['result']}")


    save_result(results, SAVE_TARGET_FILE)
    print(f"[완료] {len(results)}건 처리 — agent_result.json 저장")


if __name__ == "__main__":
    main()