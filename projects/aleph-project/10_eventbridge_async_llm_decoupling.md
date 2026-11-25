---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "10초 긴급 차단과 사후 Bedrock LLM 분석의 EventBridge 비동기 분리"
tags: ["EventBridge", "Bedrock", "Lambda", "AsyncDecoupling", "FaultIsolation", "CloudShield"]
---

# 프로젝트 제목: CloudShield — EventBridge 기반 10초 차단과 사후 LLM 분석 비동기 분리

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **역할 경계와 구현 범위:** Amazon Bedrock에 보낼 심층 분석 프롬프트와 정형 파서는 보안 직무가, 2차 심층 분석 Slack Block Kit 카드 빌더는 클라우드 B가 구현했다. 클라우드 A는 두 경로를 잇는 EventBridge 인프라(`cloudshield-threat-remediated-dev`), 오케스트레이터 이벤트 발행(`emit_threat_resolved_event`), 비동기 분석 Lambda 워커(`src/remediation/llm_worker.py`) 오케스트레이션, 그리고 결함 격리를 담당했다.
- **동기 LLM 호출이 10초 차단 SLA를 깨는 문제:** 1차 차단 Lambda(`CloudShield-Threat-Orchestrator`)는 타임아웃 10초 안에서 로그 파싱, DynamoDB 조회, L4/L7 차단을 끝내야 한다. 응답에 수 초에서 수십 초가 걸리는 Bedrock LLM 추론을 같은 Lambda 함수 안에서 동기 호출하면, LLM 지연이나 타임아웃이 1차 차단과 알림 흐름까지 끌어내린다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **EventBridge 기반 2단계 파이프라인 분리:**
  - 1차 오케스트레이터는 L4/L7 차단과 1차 Slack 알림이 끝난 직후 `Source="cloudshield.security"`, `DetailType="ThreatRemediated"` 이벤트를 EventBridge에 쏘고(`PutEvents`) 즉시 종료한다.
  - 2차 비동기 워커(`CloudShield-LLM-Analyzer`, Python 3.12, 256MB, 타임아웃 30초)가 이벤트를 받아 Bedrock Converse API(`apac.amazon.nova-micro-v1:0`) 분석과 2차 Slack 알림을 별도 프로세스에서 처리한다.
- **비대칭 결함 격리 (차단 상태 우선 원칙):**
  - EventBridge `PutEvents` 호출에서 `ClientError`가 나거나 `FailedEntryCount > 0`이 반환되어도 예외를 삼켜 로깅만 남긴다. 2차 심층 분석이 실패하더라도 이미 집행한 L4/L7 차단 상태를 롤백하지 않는다.
- **재시도 폭풍 차단과 최소 권한 IAM (`infra/terraform/modules/lambda/main.tf`):**
  - EventBridge 타깃의 `maximum_retry_attempts = 0`으로 고정해, Bedrock 타임아웃이나 Throttling 발생 시 이벤트 버스가 실패 워커를 반복 재호출해 부하를 키우는 현상을 막았다.
  - 워커 IAM 역할에는 자신의 로그 그룹(`/aws/lambda/cloudshield-llm-analyzer`) 쓰기 권한과 Bedrock 모델 호출 권한만 부여했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **EventBridge 이벤트 크기 제한과 원문 로그 절단 (`_bound_raw_logs_for_event`):**
  - 현상: 2차 LLM 분석이 공격 맥락을 읽으려면 원문 로그(`raw_logs`)를 넘겨야 하지만, 로그를 무제한 붙이면 EventBridge `PutEvents` 엔트리 크기 상한(256KB)을 넘기거나 직렬화 실패 위험이 생긴다.
  - 해결: `_bound_raw_logs_for_event`로 이벤트에 싣는 로그 건수와 길이를 일정 상한으로 잘라 페이로드 크기를 통제했다.
- **비동기 워커의 순수 격리 로딩과 남은 실행 시간 감시:**
  - `python -S` 같은 최소 격리 환경이나 공통 번들(`orchestrator.zip`, 2.73MB)에서 불필요한 임포트 충돌을 피하기 위해 `_get_incident_report_class` 등 지연 임포트 패턴을 적용했다.
  - `execute_bedrock_analysis` 실행 시 Lambda `context.get_remaining_time_in_millis()`를 확인하는 `_get_context_remaining_ms`를 두어, 30초 데드라인을 넘기기 전에 안전하게 상태를 기록하고 2차 알림 단계로 넘기도록 제어했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/remediation/orchestrator.py`, `src/remediation/llm_worker.py`, `infra/terraform/modules/lambda/main.tf`, `docs/roles/cloud-a/2026-10-21-orchestrator-putevents-worker.md`, `docs/roles/cloud-a/2026-10-23-p4-1-eventbridge-llm-deployment-report.md`
- **주요 클래스/함수:** `emit_threat_resolved_event`, `_bound_raw_logs_for_event`, `llm_analysis_handler`, `execute_bedrock_analysis`, `analyze_incident_with_bedrock`, `send_deep_analysis_slack_alert`, `_get_context_remaining_ms`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 시나리오 1(SSH)과 시나리오 2(Web)에 대해 1차 즉시 차단 -> EventBridge 발행 -> 2차 Bedrock 워커 호출 -> 2차 Slack 전파까지 이어지는 E2E 단위 통합 테스트를 구축하고, 시드니 리전 실인프라 배포 및 Trivy 보안 스캔(HIGH/CRITICAL 0건)을 마쳤다.
- **회고:** 응답 속도가 10초 이내여야 하는 차단 경로와 수십 초가 걸리는 LLM 분석 경로를 같은 실행 컨텍스트에 묶어두면 두 요구사항이 서로를 방해한다. 이벤트 버스로 두 단계의 수명 주기와 실패 영향을 끊어낸 것이 실무적인 해법이었다.
