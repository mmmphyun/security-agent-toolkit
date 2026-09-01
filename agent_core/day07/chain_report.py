# 4교시. 프롬프트 체이닝 — 요약을 다시 요약하다

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
    }
    response = requests.post(url, headers=headers, json=body)
    return response.json()["choices"][0]["message"]["content"]

def json2dict(file_path):
    with open(file_path, encoding="utf-8") as f:
        results = json.load(f)
        if results:
            return results
        return {}

def build_prompt(result):
    # 요약 프롬프트는 2교시 그대로 준비돼 있다
    prompt = """다음 보안 이벤트 처리 기록을 보고서에 넣을 한 문장으로 요약해라.
result 값의 뜻: locked=계정 잠금 실행됨, blocked=IP 차단 실행됨, held=담당자가 승인하지 않아 조치 보류됨, rejected=거부됨, watching=관찰 대상으로 등록됨.
사실만 쓰고, 글자 수 같은 사족은 붙이지 마라.
기록: """ + json.dumps(result, ensure_ascii=False)

    return prompt

'''
반복문을 통해 api 호출 횟수를 제한하는 예시 코드를 보고, 함수화하여 재귀식으로 호출해도 되겠다는 생각에 구현해봄.
하지만, LLM 응답 실패/불량에 따른 재시도 로직은 호출 스택을 소모하는 재귀(Recursion)보다 for/while 루프와 지수 백오프(Exponential Backoff)를 적용한 반복문 구조가 안전하고 표준적.
- 호출 스택(Call Stack) 누적 및 오버플로우 방지
- 대기 시간(Backoff/Jitter) 및 동기화 제어 용이성
- 반환값 및 예외 전파의 단순성
- 언어적 특성(파이썬의 TCO 미지원)
'''
def overall(summaries, depth = 0, max_depth = 3):
    general_review = ""

    if depth >= max_depth:
        return general_review
    overall_prompt = "다음은 오늘 밤 보안 이벤트 처리 요약 목록이다. 팀장에게 보고할 종합 총평을 2~3문장으로 써라. 과장 없이 사실만.\n" + summaries

    general_review = ask_llm(overall_prompt)
    depth += 1

    if len(general_review) <= 5:
        print("[검증 실패]")
        return overall(summaries, depth, max_depth)

    return general_review

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "logs", "agent_result.json")

    results = json2dict(file_path)

    summaries = ""
    for r in results:
        prompt = build_prompt(r)
        line = ask_llm(prompt)
        summaries += f"[{r['severity']}] {r['tool']} → {r['result']}: {line}\n"
        print(f"[요약] {r['tool']} → {line}")

    general_review = overall(summaries)
    print(f"[총평] {general_review}")

if __name__ == "__main__":
    main()