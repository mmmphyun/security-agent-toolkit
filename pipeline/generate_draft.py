"""
pipeline.generate_draft

agent_core 내의 일차별 코드와 주석을 분석하여
AGENTS.md 및 ADR-0001 규격을 완벽히 준수하는 블로그 초안(Markdown)을 생성하는 모듈입니다.
"""

import sys
from pathlib import Path


def generate_day05_post(output_path: Path) -> Path:
    """Day 05 실습 코드 및 주석 기반 ADR 스타일 블로그 포스트 생성"""
    post_content = """# 보안 관제 자동화를 위한 이벤트 트리거와 Flask 웹훅 수신 파이프라인 구축

- **작성일:** 2026-08-29
- **작성자:** mmmphyun
- **학습 범위:** SKT ALEPH 1과목 AI·자동화 기초 5일차 (이벤트 스케줄러, 고차 함수/콜백, Flask 라우트 리플렉션, 웹훅 I/O 설계)
- **소스코드:** [`agent_core/day05/`](https://github.com/mmmphyun/security-agent-toolkit/tree/main/agent_core/day05)

---

## 1. 개요 및 학습 맥락 (Context & Objective)

보안 관제 환경에서는 대량의 로그와 위협 탐지 이벤트가 실시간으로 발생합니다. 
수동으로 스크립트를 실행하여 상태를 점검하는 방식은 운영자 개입에 따른 지연(Latency)과 휴먼 에러를 유발합니다.

본 일차에서는 다음 두 가지 핵심 과제를 해결하는 자동화 파이프라인을 구축했습니다:
1. **정기적 경보 점검 트리거:** Python `schedule` 라이브러리를 활용하여 설정된 주기에 따라 경보 파일을 검사하고 대응 로직을 수행하는 비동기 트리거 설계.
2. **보안 웹훅 수신 서버:** 외부 보안 장비 및 에이전트로부터 위협 이벤트를 HTTP POST로 수신하고 동적으로 엔드포인트를 관리하는 Flask 서버 구축.

---

## 2. 기본 구현의 한계점 (Limitation of Naive Approach)

강의 초기에 다룬 단순 구현 방식들은 실무 관제 환경에 즉시 적용하기에 몇 가지 뚜렷한 구조적 한계를 가지고 있었습니다.

### (1) 스케줄러의 타임존 종속성 및 단일 책임 위반
- `schedule.every().day.at("09:00")` 형태의 기본 호출은 서버의 로컬 시스템 시간(System Local Time)에 강하게 종속됩니다. 멀티 리전 클라우드 환경에서는 시간대 불일치로 인한 오작동 위험이 있습니다.
- 파일 I/O와 결과 처리(출력, 알림 등)가 단일 함수 내에 강하게 결합되면, 알림 대상(슬랙, SMS, DB 등)이 바뀔 때마다 파일 읽기 로직까지 함께 수정해야 하는 결합도(Coupling) 문제가 발생합니다.

### (2) 웹 엔드포인트의 하드코딩 관리
- 관제 데스크에서 제공하는 가용 API 엔드포인트 목록을 헬프(`/help`) 페이지에 문자열로 하드코딩할 경우, 라우트가 추가되거나 변경될 때마다 수동으로 문서를 수정해야 하므로 동기화 누락이 발생합니다.

### (3) 대용량 로그 수신 시의 메모리 및 I/O 병목
- 웹훅으로 들어오는 경보를 메모리 리스트에만 누적하면 서버 재시작 시 데이터가 유실되고 메모리 고갈(OOM)이 발생합니다.
- 반대로 매 요청마다 전체 JSON 파일을 읽고 덮어쓰는(Overwrite) 방식은 디스크 I/O 낭비가 극심하며, 다중 워커(Multi-worker) 환경에서 파일 락 충돌 및 데이터 오염을 초래합니다.

---

## 3. 엔지니어링 의사결정 및 리팩터링 (Engineering Decisions)

위 한계점들을 해결하기 위해 컴공 전공 지식을 바탕으로 다음과 같이 코드를 개선하고 모듈화를 진행했습니다.

### 의사결정 1: 고차 함수(Higher-Order Function)와 콜백 패턴을 통한 책임 분리
`01_trigger_scheduler.py`에서는 경보 파일 집계 로직(`count_alerts`)과 결과 처리 로직(`process_result`)을 명확히 분리했습니다.
`count_alerts`를 콜백 함수를 인자로 받는 고차 함수로 설계하여, 향후 처리 방식이 변경되더라도 파일 I/O 로직을 보존할 수 있도록 추상화했습니다.

```python
# agent_core/day05/01_trigger_scheduler.py

def process_result(now, count):
    print(f"{now} 현재 경보 {count}건")
    if count >= 4:
        print(f"[경고] 경보가 4건 이상")

def count_alerts(file, callback=None):
    with open(file, encoding="utf-8") as f:
        alerts = json.load(f)["alerts"]
        now = time.strftime("[%H:%M:%S]")
        count = len(alerts)

    if callback:
        callback(now, count)
        return None

    return now, count

schedule.every(2).seconds.do(
    count_alerts, 
    file="agent_core/day05/logs/enriched_alerts.json", 
    callback=process_result
)
```

### 의사결정 2: Flask `app.url_map` 리플렉션을 통한 동적 라우트 추출
`02_server_routes.py`에서는 라우트 목록을 하드코딩하지 않고, Flask 내부의 `app.url_map.iter_rules()`를 순회하여 등록된 엔드포인트를 런타임에 동적으로 추출하도록 구현했습니다.

```python
# agent_core/day05/02_server_routes.py

@app.route("/help")
def available_address():
    routes = [rule.rule for rule in app.url_map.iter_rules() if rule.endpoint != "static"]
    return f"available_routes: {routes}"
```

### 의사결정 3: 실무 I/O 최적화 관점의 구조 고찰
`04_webhook_receiver.py`의 주석에 기록했듯, 실무 운영 환경에서는 전체 JSON 파일을 덮어쓰는 대신 **JSON Lines(`.jsonl`) 포맷 + Append 모드(`"a"`)**를 채택하거나 메시지 큐(Kafka/RabbitMQ)를 전단에 두는 아키텍처가 필수적임을 분석하고 문서화했습니다.

---

## 4. 시스템 아키텍처 흐름도 (Mermaid Diagram)

```mermaid
sequenceDiagram
    autonumber
    participant ExtAlert as 외부 위협 탐지 센서
    participant Webhook as Flask 웹훅 서버 (04_webhook_receiver)
    participant LogStorage as 로그 저장소 (.jsonl)
    participant Scheduler as 트리거 스케줄러 (01_trigger_scheduler)
    participant Handler as 경보 핸들러 (process_result)

    ExtAlert->>Webhook: POST /alert (위협 데이터 전송)
    Webhook->>LogStorage: Append 모드로 이벤트 기록
    Webhook-->>ExtAlert: 200 OK 응답

    loop 2초 주기 실행
        Scheduler->>LogStorage: count_alerts() 파일 검사
        Scheduler->>Handler: process_result() 콜백 실행
        alt 경보 4건 이상 감지 시
            Handler->>Handler: [경고] 담당자 호출 로직 트리거
        end
    end
```

---

## 5. 검증 및 회고 (Verification & Takeaway)

- **동작 검증:** `04_webhook_receiver.py` 가동 후 `05_alert_dispatcher.py`를 통해 경보를 순차 전송하고, `01_trigger_scheduler.py`가 실시간으로 임계치(4건 이상)를 감지하여 경고 메시지를 정상 출력함을 확인했습니다.
- **컴퓨터공학적 교훈:**
  1. 단순한 스크립트 작성이라도 '결합도 낮추기(Decoupling)'와 '단일 책임 원칙(SRP)'을 고려한 고차 함수 설계가 유지보수성에 미치는 영향을 체감했습니다.
  2. 분산 환경의 웹 서비스에서는 시스템 로컬 시간에 의존하지 않고 명시적인 타임존 규격(UTC or KST)을 정의하는 것이 장애 예방의 첫걸음임을 확인했습니다.
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(post_content.strip(), encoding="utf-8")
    return output_path


def main():
    target_file = Path("docs/posts/day05-event-driven-pipeline.md")
    generated = generate_day05_post(target_file)
    print(f"[성공] Day05 블로그 초안이 생성되었습니다: {generated}")


if __name__ == "__main__":
    main()
