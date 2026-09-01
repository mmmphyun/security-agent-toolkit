import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

'''
표준 로깅 (logging 모듈 적용)
단순 print 로그 제거
'''
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY environment variable is missing.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "logs", "agent_result.json")
URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
DEFAULT_TIMEOUT = 15
MAX_RETRIES = 3


def ask_llm(prompt: str, retries: int = MAX_RETRIES) -> str:
    body = {
        "model": "gemini-3.5-flash-lite",
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다. 항상 한국어로 답한다."},
            {"role": "user", "content": prompt},
        ],
    }

    '''
    네트워크 안정성 및 재시도
    API 호출 타임아웃을 명시, 일시적 네트워크 장애나 속도 제한(Rate Limit)에 대응하기 위해 지수 백오프(Exponential Backoff) 기반의 재시도 로직을 적용
    '''
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(URL, headers=HEADERS, json=body, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, KeyError, IndexError) as err:
            logger.warning(f"LLM API request failed (Attempt {attempt}/{retries}): {err}")
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                logger.error("Max retries reached. Returning fallback message.")
                return "이벤트 요약 생성 실패 (API 통신 오류)"

'''
방어적 데이터 처리 및 기본값 처리
'''
def sort_key(record: Dict[str, Any]) -> int:
    return SEVERITY_RANK.get(record.get("severity", "").lower(), 99)


def read_and_sort(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Log file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    return sorted(results, key=sort_key)


def build_prompt(result: Dict[str, Any]) -> str:
    return (
        "다음 보안 이벤트 처리 기록을 보고서에 넣을 한 문장으로 요약해라.\n"
        "result 값의 뜻: locked=계정 잠금 실행됨, blocked=IP 차단 실행됨, "
        "held=담당자가 승인하지 않아 조치 보류됨, rejected=거부됨, watching=관찰 대상으로 등록됨.\n"
        "사실만 쓰고, 글자 수 같은 사족은 붙이지 마라.\n"
        f"기록: {json.dumps(result, ensure_ascii=False)}"
    )


def summarize_event(index: int, result: Dict[str, Any]) -> tuple[int, str]:
    prompt = build_prompt(result)
    line = ask_llm(prompt)
    logger.info(f"Summary generated for [{result.get('tool', 'unknown')}]")
    formatted_line = f"- [{result.get('severity', 'UNKNOWN')}] {result.get('tool', 'Unknown')} → {result.get('result', 'Unknown')}: {line}\n"
    return index, formatted_line

'''
동시성 처리 (ThreadPoolExecutor 기반 병렬 처리 함수)
LLM 요약 요청을 멀티스레드로 병렬화하여 처리 속도를 대폭 단축
'''
def generate_summaries_parallel(results: List[Dict[str, Any]], max_workers: int = 5) -> str:
    summaries_dict = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(summarize_event, idx, res): idx
            for idx, res in enumerate(results)
        }
        for future in as_completed(futures):
            idx, line = future.result()
            summaries_dict[idx] = line

    return "".join(summaries_dict[i] for i in range(len(results)))


def overall(summaries: str) -> str:
    overall_prompt = (
        "다음은 오늘 밤 보안 이벤트 처리 요약 목록이다. "
        "팀장에게 보고할 종합 총평을 2~3문장으로 써라. 과장 없이 사실만.\n"
        f"{summaries}"
    )
    general_review = ask_llm(overall_prompt)
    if len(general_review) < 5 or "생성 실패" in general_review:
        logger.warning("General review validation failed or API error occurred.")
        return "종합 총평 생성에 실패하여 원시 데이터를 확인해야 합니다."

    logger.info("General review generation completed.")
    return general_review


def analyze_log(results: List[Dict[str, Any]]) -> Dict[str, int]:
    count = {"high": 0, "held": 0, "total": len(results)}
    for r in results:
        if r.get("severity") == "high":
            count["high"] += 1
        if r.get("result") == "held":
            count["held"] += 1
    return count


def write_report(today: date, analyzed_log: Dict[str, int], summaries: str, general_review: str) -> str:
    return f"""# 야간 보안 관제 보고 ({today})

## 한눈에 보기
- 처리한 경보: 실행 {analyzed_log['total']}건 (high {analyzed_log['high']}건) / 보류 {analyzed_log['held']}건
- **주의: high 경보 {analyzed_log['high']}건 — 건별 내역을 먼저 확인할 것**

## 건별 내역 (위험한 것부터)
{summaries}
## 총평
{general_review}"""


def save_report(file_path: str, report: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Report successfully saved to {file_path}")


def main() -> None:
    try:
        sorted_results = read_and_sort(FILE_PATH)
        if not sorted_results:
            logger.warning("No security events found to process.")
            return

        summaries = generate_summaries_parallel(sorted_results)
        general_review = overall(summaries)
        analyzed_log = analyze_log(sorted_results)

        today = date.today()
        folder = os.path.join(BASE_DIR, "reports", today.strftime("%Y-%m"))
        file_path = os.path.join(folder, f"daily_report_{today}.md")

        report = write_report(today, analyzed_log, summaries, general_review)
        save_report(file_path, report)

    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")


if __name__ == "__main__":
    main()



'''
함수 모듈화 실력 자체는 이전보다 늘었다고 생각한다.
조금 더 엣지케이스를 고려하고, 예외처리를 빼먹지 않는다면 한 단계 더 나아갈 수 있을 거라 본다.
30분도 안되는 시간 내에 모두 고려하긴 어렵지만, 해보자!
'''