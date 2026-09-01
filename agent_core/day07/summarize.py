# 2교시. 이벤트 요약 — LLM에게 기록을 읽히다

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()                    # .env 파일을 읽어 온다 (Day 4)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"   # LLM 서비스의 창구 주소
headers = {"Authorization": "Bearer " + os.getenv("GEMINI_API_KEY"), "Content-Type": "application/json"}   # 통행증(키)을 싣는 자리

def ask_llm(prompt):
    body = {
        "model": "gemini-3.5-flash-lite",
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다. 항상 한국어로 답한다."},
            {"role": "user", "content": prompt},
        ],
    }                                                            # 스키마 없음 — 자유로운 문장을 받는다
    response = requests.post(url, headers=headers, json=body)    # 요청을 보내고 응답을 받는다
    return response.json()["choices"][0]["message"]["content"]   # 응답에서 답 문장만 돌려준다


base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "logs", "agent_result.json")

with open(file_path, encoding="utf-8") as f:
    results = json.load(f)

summaries = ""                       # 요약을 모을 글자 묶음
for r in results:
    prompt = """다음 보안 이벤트 처리 기록을 보고서에 넣을 한 문장으로 요약해라.
result 값의 뜻: locked=계정 잠금 실행됨, blocked=IP 차단 실행됨, held=담당자가 승인하지 않아 조치 보류됨, rejected=거부됨, watching=관찰 대상으로 등록됨.
사실만 쓰고, 글자 수 같은 사족은 붙이지 마라.
기록: """ + json.dumps(r, ensure_ascii=False)
    line = ask_llm(prompt)
    summaries += f"- [{r['severity']}] {r['tool']} → {r['result']}: {line}\n"
    print(f"[요약] {r['tool']} → {line}")

print(summaries)