# 6교시. 종합 실습 — 보고하는 관제 데스크
import json
import os
from datetime import date

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "logs", "agent_result.json")
RANK = {"high": 0, "medium": 1, "low": 2}
URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
HEADERS = {"Authorization": "Bearer " + os.getenv("GEMINI_API_KEY"), "Content-Type": "application/json"}

def ask_llm(prompt):
    body = {
        "model": "gemini-3.5-flash-lite",
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다. 항상 한국어로 답한다."},
            {"role": "user", "content": prompt},
        ],
    }
    response = requests.post(URL, headers=HEADERS, json=body)
    return response.json()["choices"][0]["message"]["content"]

def sort_key(r):
    severity = r["severity"]
    return RANK[severity]

def read_and_sort(file_path):
    with open(file_path, encoding="utf-8") as f:
        results = json.load(f)
    
    return sorted(results, key=sort_key)

def build_prompt(result):
    prompt = """다음 보안 이벤트 처리 기록을 보고서에 넣을 한 문장으로 요약해라.
    result 값의 뜻: locked=계정 잠금 실행됨, blocked=IP 차단 실행됨, held=담당자가 승인하지 않아 조치 보류됨, rejected=거부됨, watching=관찰 대상으로 등록됨.
    사실만 쓰고, 글자 수 같은 사족은 붙이지 마라.
    기록: """ + json.dumps(result, ensure_ascii=False)

    return prompt

def summarize(prompt, result):
    line = ask_llm(prompt)
    print(f"[요약] {result['tool']} → {line}")

    return f"- [{result['severity']}] {result['tool']} → {result['result']}: {line}\n"

def overall(summaries):
    overall_prompt = f"다음은 오늘 밤 보안 이벤트 처리 요약 목록이다. 팀장에게 보고할 종합 총평을 2~3문장으로 써라. 과장 없이 사실만.\n{summaries}"
    general_review = ask_llm(overall_prompt)
    if len(general_review) < 5:
        print("[검증 실패] 총평이 비어 있다 — 다시 실행하자")
    print("[총평] 생성 완료")

    return general_review

def analyze_log(results):
    count = {"high": 0, "held": 0}
    for r in results:
        if r["severity"] == "high":
            count['high'] += 1
        if r["result"] == "held":
            count['held'] += 1
    count['total'] = len(results)

    return count
    
def write_report(today, analyzed_log, summaries, general_review):
    report = f'''# 야간 보안 관제 보고 ({today})

## 한눈에 보기
- 처리한 경보: 실행 {analyzed_log['total']}건 (high {analyzed_log['high']}건) / 보류 {analyzed_log['held']}건
- **주의: high 경보 {analyzed_log['high']}건 — 건별 내역을 먼저 확인할 것**

## 건별 내역 (위험한 것부터)
{summaries}

## 총평
{general_review}'''
    
    return report

def save_report(file_path, report):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"[완료] {f.name} 저장")


def main():
    sorted_results = read_and_sort(FILE_PATH)

    summaries = ""
    for result in sorted_results:
        prompt = build_prompt(result)
        summaries += summarize(prompt, result)

    general_review = overall(summaries)

    today = date.today()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "reports", today.strftime("%Y-%m"))
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"daily_report_{today}.md")

    report = write_report(today, analyze_log(sorted_results), summaries, general_review)
    save_report(file_path, report)

if __name__ == "__main__":
    main()