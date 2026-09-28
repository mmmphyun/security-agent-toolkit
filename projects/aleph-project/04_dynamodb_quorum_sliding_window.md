---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "분산 환경의 상태 보존과 쿼럼 일관성: CloudWatch 배치 분할과 DynamoDB 3-버킷 윈도우"
tags: ["DynamoDB", "DistributedSystems", "Quorum", "EventualConsistency", "SlidingWindow", "CloudShield"]
---

# 프로젝트 제목: CloudShield — 분산 상태 보존과 정족수 일관성: DynamoDB 3-버킷 슬라이딩 윈도우

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **배치 분할 인입 시 무상태(Stateless) 룰 엔진의 탐지 누락:** AWS CloudWatch Logs Subscription Filter는 버퍼 크기 정책에 따라 단일 공격의 실패 로그를 복수의 Lambda 호출 배치로 분할 전달한다. 단일 배치의 메모리만 검사하는 룰 엔진은 5회 임계치 공격이 3건 + 2건으로 쪼개질 경우 탐지를 100% 누락하는 치명적 한계를 노출했다.
- **네트워크 실측(176ms)과 사후 L4 격리의 당위성:** 패킷 캡처 실측 결과 SSH 3-Way Handshake부터 4-Way FIN까지의 세션 수명은 176.109ms에 불과했다. 비동기 로그 수신 시점에 세션은 이미 종료되었으므로, 분할 배치를 영속 계층에 누적하여 5회 도달 즉시 다음 6번째 세션의 TCP SYN을 차단하는 사후 L4 격리 아키텍처가 필수적이었다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **Shared-Nothing Lambda 환경과 DynamoDB 물리 매핑:**
  - Lambda는 Firecracker MicroVM 내부의 격리된 주소 공간을 가지므로 외부 분산 영속 계층이 필수적이다.
  - 파티션 키(`BF#<ip>#<user>#{epoch // 300}`)는 MD5 해시 링을 통해 특정 스토리지 노드의 물리 메모리/SSD 파티션 블록으로 $O(1)$ 직렬 라우팅되는 전역 메모리 포인터 역할을 수행한다.
- **단일 키 OCC 경합 폐기와 시간 버킷 파티셔닝(Lock-Free):**
  - 단일 키 기반 낙관적 락(OCC, `ConditionExpression="expire_at >= :now"`)은 밀리초 단위 동시 인입 시 재시도 소진으로 인한 데이터 유실과 지연시간 스파이크를 유발했다.
  - 파티션 키에 시간 버킷 ID를 포함하여 만료 판별 조건식을 완전히 제거하고, 스토리지 노드의 단일 리더 스레드가 직접 `list_append`를 수행하는 **락 프리(Lock-Free) 원자적 Upsert** 구조로 전환했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **분산 복제 쿼럼($R + W > N$)과 Stale Read 방어:**
  - DynamoDB는 3개 가용영역($N=3$)에 복제 노드를 유지하며 과반수 쓰기($W=2$, Paxos Leader + 1 Follower) 완료 즉시 200 OK를 반환한다.
  - 3번째 노드로의 복제가 지연된 수십 ms 시구간에 `ConsistentRead=False`($R=1$)로 조회하면 지연 노드를 읽어 5회 도달 상태를 4회로 오독하는 Stale Read 결함이 발생했다.
  - 직전/현재/직후 3개 버킷 조회 시 `ConsistentRead=True`($R=2$)를 강제하여 정족수 부등식 $W(2) + R(2) = 4 > N(3)$을 만족시켰고, 비둘기집 원리에 의해 최신 쓰기 노드가 반드시 조회 결과에 포함되도록 보장했다.
- **쿼럼과 LSN(Log Sequence Number) 동점 해소 메커니즘:**
  - 2개 노드 응답이 `[최신 쓰기(v2), 지연 노드(v1)]`로 1:1 동점일 때 다수결 투표가 불가능하므로, 스토리지 엔진 내부의 LSN(Log Sequence Number)과 타임스탬프를 대조하여 최신 버전을 선별하는 메커니즘을 규명했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/remediation/auth_window.py`, `tests/unit/test_auth_window.py`, `infra/terraform/dynamodb.tf`
- **주요 클래스/함수:** `record_failure`, `check_threat`, `_get_bucket_key`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 분할 배치 인입 시에도 락 프리 Upsert와 강력한 일관성 읽기(ConsistentRead)를 통해 100% 무누락 탐지와 충돌률 0%를 동시에 달성했다.
- **교훈:** 분산 데이터베이스에서 고가용성(AP)과 정합성(CP)의 트레이드오프가 단일 클라이언트 파라미터(`ConsistentRead`) 뒤에 은닉되어 있음을 실증했다.
