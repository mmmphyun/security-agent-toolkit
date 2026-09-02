# 6교시. 종합 실습 — 완성과 회고

import json
import os
from datetime import date

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = "config.json"
CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_FILE)
LOG_FILE = "enriched_alerts.json"
LOG_PATH = os.path.join(BASE_DIR, "logs", LOG_FILE)

# 1) 연결·설정 준비 — Day 4 + 1교시
load_dotenv()                    # .env 파일을 읽어 온다 (Day 4)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"   # LLM 서비스의 창구 주소
headers = {"Authorization": "Bearer " + os.getenv("GEMINI_API_KEY"), "Content-Type": "application/json"}   # 통행증(키)을 싣는 자리

with open(CONFIG_PATH, encoding="utf-8") as f:   # 설정 파일을 읽는다 (1교시)
    config = json.load(f)

SEVERITY_ORDER = ["low", "medium", "high"]           # 게이트 "이상" 판정용 순위표 (1교시)

# 2) LLM 호출 — 스키마가 필요하면 넘겨받는다
def ask_llm(prompt, response_format=None):
    body = {
        "model": config["model"],                    # 모델 이름은 설정에서
        "messages": [
            {"role": "system", "content": "너는 보안 관제 어시스턴트다. 항상 한국어로 답한다."},
            {"role": "user", "content": prompt},
        ],
    }
    if response_format is not None:                  # 판단은 스키마로, 요약은 자유 문장으로
        body["response_format"] = response_format
    response = requests.post(url, headers=headers, json=body)
    return response.json()["choices"][0]["message"]["content"]

def parse_judgment(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("[파싱 실패] JSON이 아니다:", text[:40])
        return None

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

# 3) 도구 상자 — Day 6
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

# 4) 판단 담당 — Day 6 종합 실습을 함수로 묶었다 (3교시)
def run_desk():
    with open(LOG_PATH, encoding="utf-8") as f:
        report = json.load(f)
    results = []
    for alert in report["alerts"]:
        prompt = "다음 보안 경보를 판단해라.\n경보: " + json.dumps(alert, ensure_ascii=False) + """

쓸 수 있는 도구 목록:
- lock_account: 계정이 공격받고 있을 때 그 계정을 잠근다
- block_ip: 특정 IP가 공격을 보낼 때 그 IP를 차단한다
- watch: 확실하지 않을 때 관찰 대상으로만 등록한다"""
        answer = ask_llm(prompt, JUDGMENT_FORMAT)
        judgment = parse_judgment(answer)
        if judgment is None:
            continue
        print(f"[판단] {alert['rule']} → {judgment['severity']} — {judgment['summary']}")
        name = judgment["tool"]
        if name not in tools:
            print(f"[거부] {name} — 허용 목록에 없는 도구")
            judgment["result"] = "rejected"
            results.append(judgment)
            continue
        if SEVERITY_ORDER.index(judgment["severity"]) >= SEVERITY_ORDER.index(config["approve_severity"]):   # 기준 "이상"이면 게이트 — 순위 비교 (1교시)
            approve = input(f"{name} 조치를 실행할까요? (y/n) ")
            if approve != "y":
                print(f"[보류] {alert['rule']} — 담당자가 승인하지 않음")
                judgment["result"] = "held"
                results.append(judgment)
                continue
        judgment["result"] = tools[name](alert)
        results.append(judgment)
    return results                                   # 다음 단계에 넘겨줄 값 (3교시)

# 5) 보고 담당 — Day 7 종합 실습을 함수로 묶었다 (3교시)
RANK = {"high": 0, "medium": 1, "low": 2}
def sort_key(r):
    severity = r["severity"]
    return RANK[severity]

def run_report(results):
    results = sorted(results, key=sort_key)
    summaries = ""
    for r in results:
        prompt = """다음 보안 이벤트 처리 기록을 보고서에 넣을 한 문장으로 요약해라.
result 값의 뜻: locked=계정 잠금 실행됨, blocked=IP 차단 실행됨, held=담당자가 승인하지 않아 조치 보류됨, rejected=거부됨, watching=관찰 대상으로 등록됨.
사실만 쓰고, 글자 수 같은 사족은 붙이지 마라.
기록: """ + json.dumps(r, ensure_ascii=False)
        line = ask_llm(prompt)
        print(f"[요약] {r['tool']} → {line}")
        summaries = summaries + f"- [{r['severity']}] {r['tool']} → {r['result']}: {line}\n"
    overall = ask_llm("다음은 오늘 밤 보안 이벤트 처리 요약 목록이다. 팀장에게 보고할 종합 총평을 2~3문장으로 써라. 과장 없이 사실만.\n" + summaries)
    high_count = 0
    for r in results:
        if r["severity"] == "high":
            high_count = high_count + 1
    today = date.today()
    if high_count > 0:
        warning = f"**주의: high 경보 {high_count}건 — 건별 내역을 먼저 확인할 것**"
    else:
        warning = "특이 사항 없음"
    report = f"""# 야간 보안 관제 보고 ({today})

## 한눈에 보기
- 처리한 경보: {len(results)}건 (high {high_count}건)
- {warning}

## 건별 내역 (위험한 것부터)
{summaries}
## 총평
{overall}
"""
    folder = os.path.join(BASE_DIR, config['report_folder'], today.strftime("%Y-%m"))   # 폴더 이름도 설정에서
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"daily_report_{today}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[완료] {filename} 저장")
    return filename                                  # 다음 단계에 넘겨줄 값 (3교시)

# 6) 알림 담당 — 2교시
def notify(filename):
    try:
        requests.post(config["webhook_url"], json={"rule": "daily_report", "file": filename})
        print("[알림] 웹훅 전송 완료")
    except requests.exceptions.ConnectionError:
        print("[알림 실패] 서버가 꺼져 있다 — 보고서는 저장됐으니 데스크는 멈추지 않는다")
    print("(notify 끝)")


# 7) 지휘부 — 3교시
def main():
    results = run_desk()
    report = run_report(results)
    notify(report)
    print(f"[파이프라인 완료] 판단 {len(results)}건 → {report}")


if __name__ == "__main__":
    main()



'''
7일간 개선해온 방향으로 수정하기에는 소요가 너무 커서 8일차 6교시 스켈레톤 코드에서 파일 경로 외 고친 것 없음.

Q. 코드 수정하는게 너무 귀찮아서, 말로 모듈화 진행.
    run_desk()부터.
    로그 파일 읽어오는거 하나, 프롬프트 빌드하는거 하나. result를 만들어서 내보내는건 run_desk()가 해야하는게 맞아보이기는 하는데, 중간 출력부를 따로 하나 함수로 빼야할까?
    다음 run_report(results).
    요약(summaries) llm에게 요청 후 반환하는거 하나, results 분류하는거 하나, report 작성하는거 하나.
A. 책임 분리와 실무 아키텍처 관점에서는 몇 가지 치명적인 누락과 과설계 존재.
    run_desk():
        - 출력부 분리 여부: 무의미. 로깅 모듈 적용 또는 별도 함수로 뺀다면 단순 출력이 아니라, "외부 보안 시스템(방화벽, IAM) 호출 액션 로깅 및 감사(Audit) 로그 기록" 책임으로 격리
        - 인터랙티브 승인 게이트의 분리 누락: 승인 판정 로직(check_approval_policy)과 실제 승인 수집 인터페이스(request_human_approval)를 반드시 분리해야 CLI/슬랙 인터랙션 등으로 확장 가능
        - 도구 디스패처(Action Dispatcher) 분리: tools[name](alert)를 실행하고 실패 시 예외 처리하는 실행기를 분리해야, 액션 실패(예: 방화벽 API 타임아웃) 시 파이프라인 전체가 죽는 문제를 방지
    run_report(results):
        - 요약 요청, 결과 분류(정렬/집계), 보고서 작성 3분할은 적절
        - 파일 I/O 및 저장소(Storage) 책임 분리 누락: 보고서 내용 마크다운 렌더링(render_markdown_report)과 파일 저장(save_report_file)을 분리하지 않으면,
                                                    로컬 파일 대신 S3/R2 업로드나 이메일 전송으로 요구사항이 바뀔 때 보고서 생성 로직까지 뜯어고쳐야 함
        - N+1 LLM 호출 비효율: 배치(Batch) 프롬프트 구조로 묶거나 정형 데이터는 템플릿 엔진(Jinja2 등)으로 처리하고 비정형 종합 요약만 LLM에 위임하는 구조로 설계해야 비용과 레이턴시를 방어

```
[Desk 모듈]
├── load_alerts(file_path) -> List[dict]                  # 로그 파일 안전 로드
├── build_judgment_prompt(alert) -> str                   # 프롬프트 구성
├── is_approval_required(severity, config_level) -> bool  # 게이트 판정
├── prompt_approval_gate(rule, action) -> bool            # 승인 입력 인터페이스
└── execute_remediation(tool_name, alert) -> str          # 도구 실행 및 예외 격리

[Report 모듈]
├── aggregate_metrics(results) -> dict                    # 위험도 순 정렬 및 카운트 집계
├── generate_summaries(results) -> tuple[str, str]        # LLM 요약 및 총평 생성
├── render_markdown(metrics, summaries, today) -> str     # 템플릿 기반 리포트 문자열 생성
└── save_report(content, base_dir, folder_name) -> str    # 경로 생성 및 파일 I/O
```

Q. 파일을 나눈다면?
A. 기능별로만 나누는 것이 아니라, 설정/외부 통신(인프라) - 비즈니스 코어(도메인) - 파이프라인 진입점(오케스트레이션)으로 역할을 격리

```
security_pipeline/
├── config.json                     # 기본 정적 설정값
├── .env                            # 민감 정보 (API 키, 웹훅 URL)
├── main.py                         # 파이프라인 오케스트레이터 (진입점): 비즈니스 로직을 직접 구현하지 않고, 각 모듈의 함수를 호출하여 데이터 흐름(alerts -> desk -> report -> notify)만 제어
│
├── core/
│   ├── config.py                   # .env + config.json 통합 로더 및 유효성 검증
│   └── llm.py                      # Gemini API 클라이언트 및 스키마 호출 전담: 프롬프트 전달, 타임아웃, 예외 처리, 응답 JSON 파싱 책임만
│
├── desk/
│   ├── alerts.py                   # 로그 파일(JSON) 파싱 및 유효성 검사
│   ├── evaluator.py                # LLM 프롬프트 빌드 및 판단 결과 파싱
│   ├── gate.py                     # 승인 임계값 판정 및 사용자 승인 인터페이스: 프롬프트 전달, 타임아웃, 예외 처리, 응답 JSON 파싱 책임만
│   └── tools.py                    # 보안 조치 액션 (차단, 잠금, 관찰) 실행기: 프롬프트 전달, 타임아웃, 예외 처리, 응답 JSON 파싱 책임만
│
├── report/
│   ├── aggregator.py               # 결과 정렬, 통계 집계(high count 등)
│   ├── summarizer.py               # LLM 기반 건별 요약 및 총평 생성
│   └── writer.py                   # 마크다운 렌더링 및 로컬 파일 시스템 저장: 텍스트를 파일로 저장하는 I/O만 전담
│
└── notification/
    └── webhook.py                  # 슬랙/디스코드 웹훅 전송 및 재시도/에러 격리
```
'''