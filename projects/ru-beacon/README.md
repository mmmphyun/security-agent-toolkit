# Ru-Beacon 기술 회고 및 연재 계획

마인크래프트(Minecraft) 서버와 디스코드(Discord) 커뮤니티를 실시간 연동하고, 이벤트 기반 DAG 워크플로우를 분산 동시성 제어 하에 처리하는 클라우드 네이티브 SaaS 플랫폼(Ru-Beacon)의 엔지니어링 회고 시리즈 계획입니다.

---

## 연재 시리즈 로드맵

### 1편. 기존 연동 한계 극복과 분산 아키텍처 설계
- **파일명:** `01_architecture_and_design.md`
- **시점:** 알파 배포 직전
- **주요 내용:**
  - 모놀리식 봇 및 1:1 플러그인 연동의 마인크래프트 메인 틱(TPS) 간섭, 비정형 소켓 통신의 한계 (Why)
  - Event-Driven Hexagonal + CQRS 분리 아키텍처 선정 배경
  - Spring Boot 대비 Kotlin Coroutine 스택(Ktor, Exposed, Kord) 채택에 따른 트레이드오프 (FinOps 및 자원 격리)
  - WSS 양방향 프레임 계약과 2-Tier 분산 동시성 제어(Redis Lua + DB Atomic Update) 설계

### 2편. K3s/KEDA 기반 클라우드 알파 배포 및 부하 분산 트러블슈팅
- **파일명:** `02_alpha_benchmark_troubleshooting.md`
- **시점:** 알파 테스트 완료 후
- **주요 내용:**
  - k6 기반 1,000 RPS 분산 동시성 벤치마크 및 병목 분석
  - 코루틴 워커의 CPU 메트릭 맹점과 KEDA Redis Streams Consumer Lag 기반 오토스케일링(HPA) 구축
  - 고부하 상황에서의 1차 Lua Fast-Fail 실측(평균 1.82ms, P99 4.12ms) 검증
  - 비동기 WSS I/O와 Bukkit 메인 틱 동기 디스패치 간 경합 제어

### 3편. 베타 프로덕션 운영 및 데이터 무결성 보장
- **파일명:** `03_beta_production_operations.md`
- **시점:** 베타 프로덕션 운영 후
- **주요 내용:**
  - 실 유저 트래픽 유입 시 Thundering Herd 방어 및 정원 초과 Fast-Fail 운영 실적
  - Dual-Write(Redis-PostgreSQL) 불일치 방지를 위한 보상 트랜잭션 및 정합성 보장
  - 분산 감사 로그(Audit Log) 기반 추적성 확보와 프로덕션 무중단 패치/롤백 경험
