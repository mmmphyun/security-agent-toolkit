---
repo: "https://github.com/mmmphyun/rpg_sync_project"
topic: "물리적 인프라 제약 환경에서 교과서적 이상론을 버리고 병목을 뚫은 4가지 실용적 타협 (Part 6)"
tags: ["Pragmatic-Engineering", "Decision-Matrix", "Database-Pool", "AsyncIO", "FastAPI", "Redis-Lock", "SSR-Optimization"]
---

# 프로젝트 회고 Part 6: 교과서적 이상론을 버리고 병목을 뚫다 — 물리적 제약 환경에서의 4가지 실용적 타협

## 1. 프로젝트 시작 배경: 태평양 횡단 RTT 200ms와 1GB RAM의 물리적 한계 (Why)

아키텍처 교과서나 프레임워크 문서는 항상 가장 이상적인 패턴을 권장한다. 풀에서 커넥션을 대여할 때마다 `SELECT 1`로 사전 검증하고, 모든 I/O는 비동기 드라이버로 전환하며, 분산 락은 Watchdog 데몬으로 갱신하고, 프론트엔드는 SPA로 분리하라는 식이다.

그러나 본 프로젝트가 마주한 실제 운영 인프라는 극단적인 물리적 제약 조건을 내포하고 있었다.
- **물리적 네트워크 지연:** GCP 미국 서부 VM ↔ 한국 Supabase PostgreSQL 간의 **태평양 횡단 왕복 지연시간(RTT 200ms+)**.
- **극단적인 하드웨어 한계:** 월 0원 예산 유지를 위한 **GCP 프리티어 1GB RAM 단일 코어 VM**.
- **시간 및 공수 한계:** 1인 개발 환경에서 전체 코드베이스를 전면 재작성할 수 없는 현실적 일정.

이 물리적 제약 속에서 교과서적인 패턴을 맹신하자 시스템은 심각한 레이턴시 누적과 프로세스 다운을 겪었다. 결국 **"물리적 인프라 제약 하에서 서비스 생존과 보안은 절대 사수하고, 교과서적 순수성과 가상의 미래 트래픽 대응은 버린다"**는 일관된 판단 기준 아래 4가지 실용적 타협을 단행했다.

---

## 2. 타협 1: DB 커넥션 검증 (`SELECT 1` 사전 검증 폐기 vs 커널 TCP Keepalive + `conn.closed` + `db_retry`)

### 2.1. 이상론과 실제 병목
- **교과서적 이상론:** 풀에서 커넥션을 대여할 때마다 `SELECT 1`을 실행하여 연결 유효성을 엄격하게 사전 검증한다.
- **실제 병목:** 미국 VM에서 한국 DB로 매 쿼리마다 200ms 네트워크 지연이 선행 누적되어, 단순 3회 조회만으로도 600ms 이상의 기본 지연이 발생했다.

### 2.2. 실용적 타협
```python
# src/database/connection.py
_db_pool = pool.ThreadedConnectionPool(
    2, 8,
    dsn=os.getenv("DATABASE_URL"),
    keepalives=1,
    keepalives_idle=30,
    keepalives_interval=10,
    keepalives_count=5
)

def get_connection():
    ...
    # 소켓 통신 없이 메모리 플래그만 검사하여 0ms로 즉시 대여
    if conn.closed != 0:
        raise OperationalError("Connection is closed.")
    return conn
```
- 소켓 통신을 하지 않고 프로세스 메모리의 `conn.closed` 플래그만 검사하여 0ms로 즉시 반환한다.
- TCP Half-Open 사각지대는 OS 커널 수준의 TCP Keepalive(30초 유휴 시 10초 간격 5회 프로브)를 풀 초기화 옵션에 주입하여 좀비 소켓을 50초 내 강제 정리하도록 방어했다.
- 만약의 연결 단절 예외(`OperationalError`, `psycopg2.DatabaseError`)는 사후 `@db_retry(max_retries=2)` 데코레이터에서 풀에서 폐기 후 1회 재연결하여 투명하게 복구했다.

### 2.3. 의사결정 기준 (Decision Matrix)
- **넘어간 부분 (타협):**
  - **사전 완결성:** 모든 커넥션이 쿼리 실행 전 살아있음을 원격 왕복으로 확인해야 한다는 이상론.
  - **예외 발생 허용:** 극히 드문 유휴 연결 단절 시 첫 1회 쿼리가 실패(Fail-fast)하고 재시도 비용이 발생하는 것을 수용.
- **절대 타협하지 않은 부분 (사수):**
  - **정상 요청(99%)의 지연시간:** 200ms 왕복 지연을 매 요청마다 강제로 지불하지 않도록 방어.
  - **서비스 크래시 방지:** 커널 Keepalive와 `@db_retry` 자가 치유로 프로세스 중단 없이 최종 성공 보장.
- **판단 기준:**
  > *"1%의 예외 상황을 잡기 위해 99%의 정상 요청에 200ms 지연 세금을 물리는 것은 안티패턴이다."*

---

## 3. 타협 2: 비동기 I/O 전환 (`psycopg2` + ThreadPool vs `asyncpg` 전면 재작성)

### 3.1. 이상론과 실제 병목
- **교과서적 이상론:** FastAPI와 discord.py의 비동기 이벤트 루프 표준에 맞춰 전체 DB 레이어를 `asyncpg` 등 비동기 드라이버로 전면 재작성한다.
- **실제 병목:** 기존 `psycopg2` 동기 쿼리가 비동기 단일 스레드 루프를 점유하여 Discord Gateway Heartbeat 패킷이 지연되었고, 봇이 게이트웨이로부터 강제 연결 종료당하는 장애가 반복 발생했다.

### 3.2. 실용적 타협
```python
# src/bot/main.py
loop = asyncio.get_running_loop()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
loop.set_default_executor(executor)
```
- 비동기 드라이버 마이그레이션을 회피하고, 봇 메인 루프에 전용 스레드풀(`max_workers=20`)을 주입하여 동기 호출을 워커 스레드로 완전 격리했다.
- `docker-compose.yml` 상에서 `discord-bot`과 `web-app` 컨테이너를 물리적으로 분리하여 스레드 경합을 방지했다.
- DB 커넥션 풀을 `minconn=2, maxconn=8`로 엄격히 통제하고, 웹 라우터(`src/web/main.py`)에서는 10분 TTL의 Redis 캐시(`cache:jobs:all`)로 요청을 선제 흡수하여 8개 커넥션 한도 내에서 세션 고갈을 원천 차단했다.

### 3.3. 의사결정 기준 (Decision Matrix)
- **넘어간 부분 (타협):**
  - **아키텍처 순수성:** 이벤트 루프 전체가 완전한 논블로킹이어야 한다는 이상론.
  - **가상의 고동시성:** 수만 동시 요청을 소화해야 한다는 미래 트래픽 오버엔지니어링.
- **절대 타협하지 않은 부분 (사수):**
  - **디스코드 봇의 생명선:** DB 쿼리로 인해 루프가 멈춰 봇이 죽는 사태 원천 차단.
  - **납기 및 개발 리소스:** 검증된 수십 개의 동기 비즈니스 함수를 갈아엎는 비효율적인 공수 낭비 거부.
- **판단 기준:**
  > *"현재 유저 규모에서 필요한 동시성은 20개 워커 스레드와 캐시 계층으로 충분하며, 봇의 연결 유지가 비동기 코드의 교과서적 순수성보다 우선한다."*

---

## 4. 타협 3: 분산 락 설계 (Safe TTL 15초 vs Watchdog / Redlock)

### 4.1. 이상론과 실제 병목
- **교과서적 이상론:** 다중 노드 분산 락(Redlock)을 구현하고, 락 점유 중 만료되지 않도록 백그라운드 갱신 스레드(Watchdog)로 만료 시간을 계속 연장한다.
- **실제 병목:** 디스코드 관리자 인터랙션(스태프의 유저 우회 승인/거절 버튼)은 처리 시간이 100~300ms에 불과하다. 이 초단기 UI 멱등성 보장을 위해 Watchdog 데몬 스레드와 복잡한 분산 합의를 얹는 것은 명백한 오버엔지니어링이었다.

### 4.2. 실용적 타협
```python
# src/bot/cogs/users/reason_bypass.py
lock_key = f"rpgsync:processing_reason:{mc_uuid}"
acquired = await redis_client.set(lock_key, "1", ex=15, nx=True)
if not acquired:
    await interaction.response.send_message("이미 처리 중이거나 완료된 사유입니다.", ephemeral=True)
    return

try:
    await interaction.response.defer()
    # 버튼 비활성화 및 Redis Pub/Sub 발행 (소요 시간 100~300ms)
    ...
finally:
    await redis_client.delete(lock_key)
```
- 대상 유저의 UUID 단위로 격리된 단발성 락(`SET NX EX 15s`)을 적용하고, `try ... finally` 블록에서 명시적으로 해제했다.
- 비즈니스 로직 소요 시간(100~300ms) 대비 15초 TTL은 50배 이상의 안전 마진을 제공하므로 로직 수행 중 락이 자동 만료될 위험이 0에 수렴한다.
- Redis 컨테이너에 `maxmemory 50mb --maxmemory-policy volatile-lru`를 설정하여 1GB RAM 호스트의 OOM 위험을 물리적으로 차단했다.

### 4.3. 의사결정 기준 (Decision Matrix)
- **넘어간 부분 (타협):**
  - **학술적 분산 합의 및 무한 안전성:** 15초를 초과하는 비정상 장기 트랜잭션 상황에서도 락이 유지되어야 한다는 극단적 엣지 케이스.
  - **락 자동 연장 메커니즘:** 백그라운드 갱신 데몬(Watchdog)의 정밀함.
- **절대 타협하지 않은 부분 (사수):**
  - **시스템 복잡도 통제:** 300ms 내 완료되는 단순 UI 멱등성 작업에 불필요한 상태 관리 데몬을 추가하지 않음.
  - **중복 처리 방지:** 동일 관리자의 연타(따닥) 클릭 및 복수 관리자의 동시 승인으로 인한 상태 충돌 방어.
- **판단 기준:**
  > *"300ms 내에 끝나는 단순 UI 버튼 중복 클릭 방지에 분산 락 갱신 데몬을 띄우는 것은 닭 잡는 데 소 잡는 칼을 쓰는 꼴이다. 15초 Safe TTL이면 충분하다."*

---

## 5. 타협 4: 렌더링 방식 (Jinja2 SSR + tojson vs SPA + REST API)

### 5.1. 이상론과 실제 병목
- **교과서적 이상론:** 프론트엔드와 백엔드를 완전히 분리(SPA + REST API)하여 클라이언트 사이드 렌더링(CSR)을 구현한다.
- **실제 병목:** 브라우저 번들 로딩 후 80여 개 직업 데이터를 다시 API로 요청하면서 태평양 횡단 추가 RTT가 발생했고, 클라이언트 토큰 관리 과정에서 XSS 취약점 및 초기 깜빡임이 발생했다.

### 5.2. 실용적 타협
```html
<!-- src/web/templates/jobs.html -->
<script>
    window.INITIAL_JOBS_DATA = {{ jobs_data | tojson }};
</script>
```
- CSR을 전면 철회하고, Jinja2 템플릿 렌더링 시점에 `jobs_data`를 `window.INITIAL_JOBS_DATA`로 직접 주입하여 클라이언트 추가 호출을 0회로 단축했다.
- Jinja2 표준 `tojson` 필터를 사용하여 `<, >, &, '` 문자를 HTML 안전 문자(`\u003c`, `\u003e`)로 자동 유니코드 이스케이프함으로써 Script Tag Injection XSS를 원천 차단했다.
- 서버 라우터(`src/web/main.py`)에서 DB 원시 데이터를 그대로 노출하지 않고 필요한 필드만 화이트리스트 형태로 정제한 DTO를 주입했다.

### 5.3. 의사결정 기준 (Decision Matrix)
- **넘어간 부분 (타협):**
  - **현대적 프론트엔드 유행:** React/Vue 기반의 컴포넌트 분리 및 CSR 트렌드.
  - **관심사의 분리:** 프론트엔드와 백엔드가 완전히 분리된 REST API 아키텍처.
- **절대 타협하지 않은 부분 (사수):**
  - **보안 무결성:** `tojson` 자동 이스케이프와 화이트리스트 주입으로 XSS 공격 표면 원천 제거.
  - **초기 체감 성능:** 브라우저가 번들을 받고 다시 API를 호출하는 다단계 RTT 지연을 제거하고 첫 HTML 수신으로 렌더링 완료.
- **판단 기준:**
  > *"데이터 뷰어 성격의 대시보드에서 SPA 분리는 보안 공격 표면과 네트워크 왕복 횟수만 늘릴 뿐이다."*

---

## 6. 결론: 의사결정을 관통하는 4대 공통 원칙 (Takeaways)

1. **물리적 제약(1GB RAM, RTT 200ms)을 거스르는 이상론은 즉시 폐기한다.**
2. **"존재하지 않는 미래 트래픽"을 대비한 오버엔지니어링을 철저히 배제한다.**
3. **99%의 정상 경로 성능을 희생시켜 1%의 예외를 사전 방어하지 않고, 사후 복구(`Fail-fast & Retry`)로 해결한다.**
4. **보안(XSS/인젝션)과 프로세스 생존(Heartbeat/OOM 방지)은 어떤 상황에서도 타협하지 않는 불변의 영역으로 설정한다.**
