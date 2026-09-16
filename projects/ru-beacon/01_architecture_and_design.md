---
repo: "https://github.com/mmmphyun/ru-beacon"
topic: "마인크래프트-디스코드 실시간 연동 분산 아키텍처 및 틱 격리 설계"
tags: ["Minecraft", "Discord", "Kotlin", "Coroutines", "Ktor", "Redis-Streams", "K3s"]
---

# 프로젝트 제목: Ru-Beacon — 마인크래프트-디스코드 연동 분산 아키텍처 및 무간섭 틱 격리 설계

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **커뮤니티 운영의 파편화 및 높은 세팅 공수:** 마인크래프트 커뮤니티의 중심은 디스코드이나, 서버 개설 시 티켓, 인증, 역할 배분, 투표 등 목적별로 파편화된 다수의 봇을 각각 초대하고 권한을 분배해야 했다. 외주 시장에서 커뮤니티 세팅 대행 비용이 건당 15~30만 원에 달할 만큼 운영자에게 진입 장벽이 높았다.
- **게임 서버 영향 최소화 및 단일 플랫폼 통합:** 마인크래프트 게임 서버와 디스코드 인터랙션(모달, 버튼, 티켓)을 하나의 플랫폼으로 흡수하여 다중 봇 의존성을 없애고, 게임 서버 리소스 간섭을 최소화하는 솔루션이 필요했다.
- **비개발자 친화적 웹 대시보드 확장 및 범위 압축:** CLI 및 슬래시 커맨드 기반의 복잡한 설정 방식을 배제하고, `web-dashboard`(Next.js 14)를 통해 누구나 마우스 클릭으로 이벤트 자동화 워크플로우를 구성하고 배포/롤백할 수 있는 SaaS 플랫폼을 구축했다. 초기 기획에 포함되었던 마인크래프트 서버 자체의 TPS/메트릭 관제 기능은 시스템 결합도 완화를 위해 후속 관측성 마일스톤으로 유예하고, 이번 알파 단계에서는 커뮤니티 이벤트 자동화 및 분산 동시성 제어에 개발 역량을 집중했다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **100% Kotlin Coroutine 스택 채택 (Ktor + Exposed + Kord) 및 FinOps 극대화:**
  - Java 진영의 기본 선택지인 Spring Boot는 무거운 리플렉션과 Thread-per-request 모델로 인해 기동 시 기본 300~500MB 이상의 메모리를 잠식한다.
  - 소형 단일 노드(`K3s`)에서 월 0~20달러 미만으로 인프라를 운영하기 위해, 파드당 메모리를 100~200MB 미만으로 억제하는 경량 스택이 필수적이었다.
  - 비동기 코루틴 기반의 `Ktor`(API Ingress 및 워커), `Exposed`(경량 SQL DSL), `Kord`(디스코드 봇)를 도입하여 스레드 블로킹 없이 수백 개의 지속 연결을 소수 스레드로 수용했다.
- **통신 프로토콜 이원화 (WSS 및 Redis Streams/PubSub):**
  - 마인크래프트 플러그인과 중앙 플랫폼 통신은 REST 폴링 대신 아웃바운드 WebSocket(`WSS`) 연결을 수립하고, 일회성 인스턴스 토큰(`X-Instance-Token`)으로 테넌트와 네트워크를 인증했다.
  - VPC 내부 메시징은 단순 `Pub/Sub`의 메시지 유실(At-most-once) 취약점을 배제하고, 비즈니스 이벤트(보상, 인증, 명령)에 대해 `Redis Streams`(`XADD`, `XREADGROUP`, `XACK`, `XAUTOCLAIM`)를 배치하여 분산 워커 간 유실 없는 비동기 이벤트 소비를 보장했다. 단, 단순 인게임-디스코드 양방향 채팅은 유실 허용 특성을 고려해 경량 `Pub/Sub`로 격리했다.
- **DAG(비순환 유향 그래프) 워크플로우 엔진과 하이브리드 영속화:**
  - "디스코드 버튼 클릭 -> 인게임 접속 확인 -> 선착순 보상 지급"과 같은 조건 분기 및 순차/병렬 자동화를 위해 인메모리 DAG 디스패처를 구축했다.
  - 배포 시점에 Tarjan 강결합 컴포넌트(SCC) 알고리즘으로 순환 참조를 사전 차단하며, 워크플로우 그래프 전체는 PostgreSQL의 Versioned `JSONB` 스냅샷으로 원자적 배포와 롤백을 구현했다. 중간 스텝별 DB 저장을 없애고 코루틴(`awaitAll`) 병렬 실행 후 최종 1회 비동기 감사 로그를 기록하여 DB I/O를 최소화했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **비동기 WSS I/O와 Bukkit 단일 스레드(메인 틱) 충돌 격리 (`DEC-071`):**
  - 마인크래프트 Paper 서버는 비동기 네트워크 스레드에서 명령어(`server.dispatchCommand`)나 엔티티 조작을 직접 시도하면 `IllegalStateException: Asynchronous entity track` 크래시를 유발한다.
  - `RuBeaconPlugin`의 `executeCommandOnMainTick` 메서드에서 `server.isPrimaryThread`를 판별하고, 메인 스레드가 아닐 경우 `suspendCancellableCoroutine`과 `server.scheduler.runTask`를 결합하여 메인 틱 루프로 안전하게 작업을 넘긴 뒤 결과를 비동기 재개(Resume)하도록 격리했다.
- **재연결 폭주(Thundering Herd) 방어 (`RuBeaconWebSocketClient`):**
  - 네트워크 순단이나 마인크래프트 서버 재부팅 시 수많은 인스턴스가 동시에 WSS 재연결을 요청해 API 인그레스가 마비되는 위험이 존재했다.
  - 초기 지연 1초(`reconnectInitialDelayMs`)부터 2배씩 최대 60초(`reconnectMaxDelayMs`)까지 증가하는 지수 백오프(Exponential Backoff)에 `Random.nextLong(0, 500)` 무작위 지터를 강제 부여하여 연결 요청을 시간축으로 고르게 분산했다.
- **2-Tier Admission Control을 통한 DB 과부하 차단:**
  - 선착순 이벤트 시 다수의 유저가 동시에 버튼을 누르면 RDBMS 트랜잭션 락 경합 및 커넥션 풀 고갈이 발생할 수 있다.
  - 초기 구상 단계의 무조건적 DB 원자적 처리 방식을 기각하고, 1차 관문으로 Redis 인메모리에서 정원만큼 이벤트를 선점(Fast-Fail)한 후 2차로 DB에 일괄 영속화하는 2계층 분산 제어 방식을 설계했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
> *파이프라인이 레포지토리에서 우선적으로 정밀 분석해야 할 파일명이나 함수명 힌트*
- **핵심 파일:**
  - `minecraft-plugin/src/main/kotlin/com/rubeacon/plugin/RuBeaconPlugin.kt`
  - `minecraft-plugin/src/main/kotlin/com/rubeacon/plugin/client/RuBeaconWebSocketClient.kt`
  - `common/src/main/kotlin/com/rubeacon/common/transport/WebSocketFrame.kt`
  - `docs/TRANSPORT_PROTOCOL_SPEC.md`
  - `docs/REENGINEERING_ARCHITECTURE_BLUEPRINT.md`
- **주요 함수/클래스:**
  - `executeCommandOnMainTick` (`RuBeaconPlugin.kt`)
  - `runConnectionLoop` (`RuBeaconWebSocketClient.kt`)
  - `WebSocketFrame`, `CommandRequestPayload`, `CommandResponsePayload`
  - `suspendCancellableCoroutine`, `server.scheduler.runTask`

## 5. 결과, 배운 점 및 회고 (Results & Lessons Learned)
- **압도적인 JVM 메모리 절감과 경량화 성과:** Spring Boot 대비 극단적으로 적은 메모리 사용량을 로컬 및 테스트 환경에서 직접 확인했다. 코루틴 기반 Ktor와 Exposed 도입을 통해 JVM 프레임워크 풋프린트를 최소화하고 저비용 K3s 단일 노드 인프라의 실현 가능성을 입증했다.
- **알파 배포 시 핵심 검증 과제:** 로컬 단위/통합 테스트를 완료하고 클라우드 알파 배포를 앞둔 시점에서, 실제 원격 마인크래프트 게임 서버와의 WSS 장기 커넥션 안정성 검증을 최우선 과제로 선정했다. 향후 다중 인스턴스가 연결된 극한의 환경에서 대량 이벤트를 발생시키며 분산 큐 및 메인 틱 스케줄러의 부하 한계를 실측할 계획이다.
