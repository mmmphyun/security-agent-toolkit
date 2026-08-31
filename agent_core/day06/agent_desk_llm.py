import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from dotenv import load_dotenv
import requests

# ----------------------------------------------------------------------
# 1. 환경 설정 및 상수 정의
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
READ_TARGET_FILE = LOGS_DIR / "enriched_alerts.json"
SAVE_TARGET_FILE = LOGS_DIR / "agent_result.jsonl"

LLM_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

JUDGMENT_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "judgment",
        "schema": {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                "summary": {"type": "string"},
                "tool": {"type": "string", "enum": ["lock_account", "block_ip", "watch"]},
            },
            "required": ["severity", "summary", "tool"],
        },
    },
}

# ----------------------------------------------------------------------
# 2. 파일 I/O (영속성) 계층
# ----------------------------------------------------------------------
def load_alerts(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
        return data.get("alerts", [])

''' 단일 실패 지점(SPOF) 및 I/O 설계 결함 개선

루프 종료 후 마지막에 save_result(results, ...)로 단일 JSON 배열을 한 번에 덮어쓰던 구조를 추가 쓰기를 수행하도록 변경
'''
def append_result_jsonl(file_path: Path, record: Dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ----------------------------------------------------------------------
# 3. LLM 통신 계층
# ----------------------------------------------------------------------
def build_prompt(alert: Dict[str, Any]) -> str:
    return (
        f"다음 보안 경보를 판단해라.\n"
        f"경보: {json.dumps(alert, ensure_ascii=False)}\n"
        f"쓸 수 있는 도구 목록:\n"
        f"- lock_account: 계정이 공격받고 있을 때 그 계정을 잠근다\n"
        f"- block_ip: 특정 IP가 공격을 보낼 때 그 IP를 차단한다\n"
        f"- watch: 확실하지 않을 때 관찰 대상으로만 등록한다"
    )


def request_judgment(
    session: requests.Session, 
    api_key: str, 
    alert: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다. 항상 한국어로 답한다."},
            {"role": "user", "content": build_prompt(alert)},
        ],
        "response_format": JUDGMENT_FORMAT,
    }

    try:
        response = session.post(LLM_API_URL, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except (requests.RequestException, KeyError, json.JSONDecodeError):
        return None

# ----------------------------------------------------------------------
# 4. 도구 실행 계층
# ----------------------------------------------------------------------
''' 도구 실행 시 KeyError 발생 위험 개선

방어적 키 조회를 적용하여 스키마 불일치 시에도 프로세스가 다운되지 않도록 처리
'''
def lock_account(alert: Dict[str, Any]) -> str:
    target = alert.get("user", "UNKNOWN")
    print(f"[조치] 계정 잠금: {target}")
    return f"locked:{target}"


def block_ip(alert: Dict[str, Any]) -> str:
    target = alert.get("ip", "UNKNOWN")
    print(f"[조치] IP 차단: {target}")
    return f"blocked:{target}"


def watch(alert: Dict[str, Any]) -> str:
    rule_name = alert.get("rule", "UNKNOWN")
    print(f"[조치] 관찰 대상 등록: {rule_name}")
    return f"watching:{rule_name}"


ACTION_REGISTRY: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "lock_account": lock_account,
    "block_ip": block_ip,
    "watch": watch,
}

# ----------------------------------------------------------------------
# 5. 비즈니스 로직 및 오케스트레이션
# ----------------------------------------------------------------------
def evaluate_and_execute_tool(judgment: Dict[str, Any], alert: Dict[str, Any]) -> str:
    tool_name = judgment.get("tool")

    # 검문 1: 허용 목록 검증
    if tool_name not in ACTION_REGISTRY:
        print(f"[거부] {tool_name} — 허용 목록에 없는 도구")
        return "rejected"

    # 검문 2: High Severity 승인 게이트
    if judgment.get("severity") == "high":
        approve = input(f"{tool_name} 조치를 실행할까요? (y/n) ").strip().lower()
        if approve != "y":
            print(f"[보류] {alert.get('rule')} — 담당자가 승인하지 않음")
            return "held"

    # 조치 실행
    executor = ACTION_REGISTRY[tool_name]
    return executor(alert)


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    alerts = load_alerts(READ_TARGET_FILE)
    print(f"[*] 총 {len(alerts)}건의 경보 처리 시작")

    ''' HTTP 커넥션 오버헤드 개선
    
    with requests.Session() as session: 컨텍스트를 열고 request_judgment()에 주입하여 커넥션 풀(Connection Pool) 기반 Keep-Alive 연결을 재사용하도록 개선
    '''
    with requests.Session() as session:
        for alert in alerts:
            judgment = request_judgment(session, api_key, alert)
            if not judgment:
                print(f"[오류] LLM 분석 실패: {alert.get('rule')}")
                continue

            print(f"[판단] {alert.get('rule')} → {judgment['severity']} — {judgment['summary']}")

            judgment["result"] = evaluate_and_execute_tool(judgment, alert)
            append_result_jsonl(SAVE_TARGET_FILE, judgment)

    print(f"[*] 처리 완료 — {SAVE_TARGET_FILE.name} 저장 완료")


if __name__ == "__main__":
    main()



'''
agent_desk.py의 복잡한 작업이 뒤섞인 main()을 작업별로 함수 모듈화 하는 것에 어려움을 느꼈음
'''