import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()                    # .env 파일을 읽어 온다 (Day 4)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"   # LLM 서비스의 창구 주소
headers = {"Authorization": "Bearer " + os.getenv("GEMINI_API_KEY"), "Content-Type": "application/json"}   # 통행증(키)을 싣는 자리

JUDGMENT_FORMAT = {
    "type": "json_schema",              # 설계도 방식으로 강제한다
    "json_schema": {
        "name": "judgment",                 # 설계도 이름 (아무거나)
        "schema": {
            "type": "object",               # 답은 딕셔너리 모양
            "properties": {                 # 가질 키들
                "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                "summary": {"type": "string"},
            },
            "required": ["severity", "summary"],    # 둘 다 필수
        },
    },
}

'''
Q. llm을 사용한 보안 관제 관점에서 의도하지 않은 답변 형태나 값이 나오는 경우 이를 폐기하는지?
A. 인라인 차단 및 Fallback 메시지로 대체. 보안 관제(SIEM/SOC) 관점에서는 해당 이상 행위를 감지하기 위해 원본 응답 또는 메타데이터를 보안 로그에 기록하여 추후 분석 및 룰튜닝에 활용.
'''

def parse_judgment(text):
    try:
        judgment = json.loads(text)
        severity = ["high", "medium", "low"]

        if judgment and judgment['severity'] is not in severity:
            judgment['severity'] = 'unknown'

        return judgment
    except json.JSONDecodeError:
        print("[파싱 실패] JSON이 아니다:", text[:40])
        return None

alerts = [
    "경보: brute_force, 대상: admin, 횟수: 5회",
    "경보: night_login, 대상: admin, 시각: 03:17",
    "경보: normal_login, 대상: kim.cs, 시각: 09:12",
]

for alert in alerts:
    body = {
        "model": "gemini-3.5-flash-lite",
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다."},
            {"role": "user", "content": "다음 보안 경보를 판단해라.\n" + alert},
        ],
        "response_format": JUDGMENT_FORMAT,   # 설계도를 요청에 싣는다
    }

    response = requests.post(url, headers=headers, json=body)   # 요청을 보내고 응답을 받는다
    answer = response.json()["choices"][0]["message"]["content"]   # 응답에서 답 문장만 꺼낸다

    judgment = parse_judgment(answer)   # 글자를 딕셔너리로 — 실패하면 None

    if judgment is not None:
        print(f"[판단] {alert} → {judgment['severity']}")