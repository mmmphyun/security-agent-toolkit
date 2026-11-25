---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "Web L7 분할 로그 탐지를 위한 DynamoDB 분산 윈도우와 무음 실패 제거"
tags: ["AWS", "Lambda", "DynamoDB", "SlidingWindow", "WAFv2", "CloudShield"]
---

# 프로젝트 제목: CloudShield — Web L7 분산 위협 탐지 파이프라인과 무음 실패 제거

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **역할 경계와 구현 범위:** 웹 공격 시그니처 룰(`evaluate_web_rules`)은 보안 직무가, Nginx 접근 로그 디코더는 클라우드 B가 구현했다. 클라우드 A는 여러 Lambda 컨테이너에 나뉘어 들어오는 로그의 상태를 DynamoDB에 모으고(`src/remediation/web_window.py`), 오케스트레이터·IAM 정책과 연결하는 분산 상태 계층을 맡았다.
- **무상태 Lambda 메모리 집계 시 분할 배치 탐지 누락:** CloudWatch Logs 구독 필터가 4초 내 5회 404 스캔 로그를 3건과 2건으로 나누어 서로 다른 Lambda 컨테이너로 보내면, 프로세스 내부 `dict`만 쓰는 구조에서는 횟수가 합산되지 않아 차단이 한 번도 일어나지 않았다.
- **저장소 장애가 정상 응답으로 숨겨지는 무음 실패(Silent Failure):** 초기 오케스트레이터가 DB 오류를 내부 리스트에만 적고 `200 OK`를 반환해, AWS Lambda의 자동 재시도와 DLQ(Dead Letter Queue) 연계가 작동하지 않았다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **10초 시간 버킷 파티셔닝과 슬롯 청킹 (`WebAttackWindow`):**
  - 원리: DynamoDB는 한 항목의 최대 크기가 400KB로 제한되어 있어, 트래픽이 몰리는 IP의 로그를 단일 키에 계속 `list_append`하면 `ValidationException`이 발생하며 이후 쓰기가 모두 막힌다.
  - 설계: 파티션 키를 `WEB#{target}#{source_ip}#{bucket_id}#{slot}`(`bucket_id = int(ts) // 10`, `slot = 0..4`)으로 나누고 30초 TTL을 걸었다. 한 버킷이 포화되면 다음 슬롯으로 분산 저장하고 조회 시 활성 슬롯을 합쳐 400KB 제한을 피했다.
- **강한 일관성 읽기와 양방향 3-버킷 조회:**
  - 복제 지연으로 방금 기록한 공격 횟수가 누락되지 않도록 `ConsistentRead=True`를 적용하고, 기준 버킷(`B`)뿐 아니라 직전(`B-1`)과 직후(`B+1`) 버킷을 함께 읽어 비동기 순서 역전에 대응했다.
- **저장소 장애 시 명시적 예외 전파 (`PersistenceError`):**
  - 한 배치 안의 개별 항목 처리는 격리해 나머지 항목 처리를 끝까지 진행하되, 처리 루프가 끝난 뒤 저장소 읽기·쓰기 실패가 남아 있으면 `PersistenceError`를 상위로 `raise`해 Lambda 재시도 경로를 살렸다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **Boto3 `Table()`의 암묵적 `DescribeTable` 호출과 Silent Fallback 결함:**
  - 현상: 최소 권한 원칙에 맞춰 Lambda IAM 정책에 데이터 접근 권한(`GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`)만 주었더니 `AccessDenied`가 발생했고, 광범위 `except Exception`이 이를 삼키면서 인메모리 폴백으로 조용히 전환되었다.
  - 원리: Boto3의 리소스 모델 `dynamodb.Table(...)` 초기화나 메타데이터 접근 과정에서 `dynamodb:DescribeTable` API가 암묵적으로 호출될 수 있다.
  - 해결: 불필요한 `Table.load()` 경로를 제거하고, Terraform Lambda 모듈(`infra/terraform/modules/lambda/main.tf`) 인라인 정책에도 대상 테이블 ARN 한정으로 `dynamodb:DescribeTable`을 명시해 코드와 인프라 권한을 맞췄다.
- **후속 정상 트래픽 이후 지연 공격 배치가 들어올 때 로그가 잘리던 버그:**
  - 현상: 정상 요청($t=15\text{s}$)이 먼저 저장된 뒤, 네트워크 지연으로 늦게 도착한 공격 로그($t=0\text{-}1\text{s}$)가 탐지되지 않았다.
  - 원리: 당시 `get_active_events`가 저장된 전체 이벤트 중 가장 큰 시각(`anchor_time=15s`)을 기준으로 10초 밖 데이터(`5s` 미만)를 일괄 잘라냈기 때문이다.
  - 해결: 단일 최댓값 기준 자르기를 없애고, 현재 평가 대상 이벤트의 참조 시각(`ref_time`) 기준 양방향 구간 $[T_{ref}-10\text{s}, T_{ref}+10\text{s}]$ 안의 이벤트를 모두 전달해 룰 평가기가 전수 탐색하도록 고쳤다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/remediation/web_window.py`, `src/remediation/orchestrator.py`, `infra/terraform/modules/lambda/main.tf`, `docs/roles/cloud-a/2026-10-07-l7-distributed-threat-detection-deepdive.md`
- **주요 클래스/함수:** `WebAttackWindow`, `PersistenceError`, `parse_nginx_timestamp`, `threat_orchestrator_handler`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** Moto 가상 테스트베드에서 분할 배치(3+2), 400KB 슬롯 오버플로, 순서 역전 배치, 후속 정상 트래픽 뒤 지연 공격 유입, DB 장애 시 런타임 예외 전파까지 통합 검증을 마쳤다(당시 683개 테스트 통과).
- **회고:** 예외를 넓게 잡아 폴백으로 넘기는 코드는 겉보기에 안정적으로 보이지만 실제로는 IAM 권한 누락과 데이터 손실을 감춘다. 분산 상태 계층에서는 실패를 삼키지 않고 상위로 드러내야 인프라 재시도 메커니즘이 제 역할을 한다.
