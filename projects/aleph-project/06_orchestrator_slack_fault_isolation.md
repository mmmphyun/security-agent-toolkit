---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "오케스트레이터 파이프라인 결합과 서드파티 결함 격리: L4/L7 원자적 차단과 Slack 상황 전파"
tags: ["Orchestrator", "Lambda", "SlackAPI", "FaultIsolation", "SOAR", "CloudShield"]
---

# 프로젝트 제목: CloudShield — 엔드투엔드 위협 오케스트레이터 결합 및 서드파티 결함 격리

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **모듈 파편화 극복과 엔드투엔드 파이프라인 결합:** CloudWatch 로그 디코딩, DynamoDB 슬라이딩 윈도우 위협 판정, L4 EC2 격리, L7 WAF IPSet 차단, Slack Block Kit 알림 등 개별 개발된 모듈을 단일 서버리스 Lambda 핸들러(`threat_orchestrator_handler`)로 통합해야 했다.
- **서드파티 API 결함에 의한 보안 차단 트랜잭션 전염 방지:** Slack 웹훅 호출 실패(네트워크 순단, 500 내부 에러, Rate Limit)나 페이로드 렌더링 예외가 발생하더라도, 이미 수행 중이거나 성공한 L4/L7 차단 조치가 롤백되거나 지연되지 않도록 철저한 결함 격리(Fault Isolation)가 필수적이었다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **단일 책임 기반 핸들러 오케스트레이션 (`src/orchestrator/threat_orchestrator.py`):**
  - Lambda 진입 시 Gzip/Base64 페이로드를 역직렬화하고, `record_failure`와 `check_threat`를 순차 수행하여 임계치 초과 여부를 판정했다.
  - 위협 식별 시 L4 SG 격리와 L7 WAF 차단을 원자적으로 트리거하고, 차단 결과와 위협 메타데이터를 통합하여 Slack 보고 모듈(`reporter.py`)로 전달했다.
- **다중 계층 차단 성공 판정 가드 (`is_remediation_successful`):**
  - 단순 호출 여부가 아닌, `action_required`에 정의된 모든 필수 조치(L4, L7)가 실제로 성공했는지를 부울 연산으로 검증하여 DynamoDB 상에 `quarantined = True`를 조건부 마킹했다.
  - 조치 실패 시에는 마킹을 생략하여 후속 인입 이벤트에서 재시도가 이루어지도록 보장했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **외부 Slack API 결함 격리 (Fault Boundary):**
  - Slack 카드 전송은 독립된 `try-except` 블록으로 격리하여, 알림 발송 중 `SlackApiError`가 발생하더라도 보안 조치 결과(`remediation_result`)와 전체 핸들러 반환값(`200 OK`)을 훼손하지 않도록 통제했다.
- **10초 관통 SLA 완결 검증:**
  - 로그 인제스트부터 차단 및 알림 전파까지의 전체 레이턴시를 통합 테스트베드에서 계측하여 총 소요 시간 2~3초 이내로 10초 관통 대응 SLA를 여유 있게 충족했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/orchestrator/threat_orchestrator.py`, `src/reporter/reporter.py`, `tests/unit/test_threat_orchestrator.py`
- **주요 클래스/함수:** `threat_orchestrator_handler`, `send_slack_incident_card`, `is_remediation_successful`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 침해 공격 발생 시 로그 파싱부터 L4/L7 원자적 격리와 Slack 관제 알림까지 무중단 자동화 파이프라인을 완결했다.
- **교훈:** 보안 오케스트레이션(SOAR) 시스템에서는 부가적인 알림/관제 채널의 장애가 핵심 방어선의 차단 트랜잭션을 침범하지 못하도록 결함 격리 경계를 물리적으로 수립해야 함을 실증했다.
