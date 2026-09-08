---
repo: "https://github.com/mmmphyun/rpg_sync_project"
topic: "외부 API 장애 격리와 비동기 온보딩 파이프라인 구축 (Part 4)"
tags: ["Discord.py", "Mojang-API", "AsyncIO", "Redis-RateLimit", "UUID-Normalization", "Onboarding-Automation"]
---

# 프로젝트 회고 Part 4: 외부 API 장애 격리와 비동기 온보딩 파이프라인 구축

## 1. 문제 정의: 실시간 동기화의 복병과 인터랙션 제약 (Why)

Part 1에서 온보딩 프로세스를 자동화하기로 설계했으나, 실제 디스코드 봇과 외부 시스템을 연동하는 구현 단계에서 세 가지 현실적인 기술적 복병을 마주했다.
- **디스코드 인터랙션의 엄격한 3초 타임아웃:**
  디스코드 게이트웨이는 유저의 버튼 클릭이나 모달 제출 후 3초 이내에 ACK 응답을 받지 못하면 즉시 `Interaction failed` 오류를 반환한다.
- **해외 외부 API(Mojang)의 레이턴시와 가용성 불안정:**
  마인크래프트 정품 계정 및 고유 식별자(UUID) 검증을 위해 해외에 위치한 Mojang 공식 API(`api.mojang.com`)를 호출해야 했다. 네트워크 왕복 지연시간(RTT)과 간헐적인 Rate Limit(HTTP 429), 서비스 순단으로 인해 3초 타임아웃을 초과하거나 봇 프로세스가 블로킹되는 위험이 존재했다.
- **디스코드 API의 모달 팝업 제약과 개인정보 노출 방지:**
  디스코드 API 규격상 봇이 임의로 유저 화면에 모달을 띄울 수 없으며, 반드시 유저의 인터랙션에 응답하는 형태로만 모달을 띄울 수 있다. 또한 이용 자격 검토 과정에서 대화 기록이 공개 채널에 남지 않도록 채널 라이프사이클을 격리해야 했다.

---

## 2. 엔드투엔드 온보딩 파이프라인 아키텍처

```
[#인증 채널] ──(인증 시작 버튼)──> [MD5 해시 프라이빗 스레드 동적 생성]
                                               │
                                               ▼
                              [스레드 내 [닉네임 설정하기] 버튼 클릭]
                                               │
                                               ▼
                              [UserNicknameVerificationModal 팝업]
                                               │ (마인크래프트 계정 입력)
                                               ▼
                              [Mojang API 비동기 조회 (defer 선제 발급)]
                                               │
                       ┌───────────────────────┴───────────────────────┐
                 (검증 실패)                                      (검증 성공)
                       │                                               │
           [Redis 실패 카운트 INCR]                         [UUID 36자리 표준화 변환]
           [3회 연속 실패 시 락 및 관제 알림]                     [DB users 테이블 업서트]
                                                                       │
                                                                       ▼
                                                          [일회성 매직링크 토큰 발급]
                                                                       │
                                                                       ▼
                                                          [웹 위키 가이드 정독 및 서약]
                                                                       │
                                                                       ▼
                                                          [DB is_guide_completed 갱신]
                                                                       │
                                                                       ▼
                                                          [Redis Pub/Sub 이벤트 발행]
                                                                       │
                                                                       ▼
                                                          [봇: '뉴비' 회수 및 '멤버' 승급]
```

### 2.1. 프라이빗 스레드 격리와 유저 주도 모달 트리거
- **개인정보 노출 방지를 위한 격리 채널 (`onboarding_cmd.py:67-74`):**
  공개 채널 오염과 대화 기록 노출을 막기 위해, 유저 ID를 MD5 해싱한 고유 식별자를 기반으로 `private_thread`를 동적 생성하고 해당 유저만 초대했다.
- **버튼 기반 모달 트리거:**
  디스코드 API 제약(봇 단독 모달 호출 불가)을 준수하여, 생성된 스레드 내부로 `NicknameTriggerView` 버튼을 전송하고 유저가 직접 버튼을 클릭했을 때 `UserNicknameVerificationModal`이 노출되도록 인터랙션 체인을 구성했다.

### 2.2. 패스워드리스(Passwordless) 매직링크와 이벤트 기반 역할 승급
- **단발성 매직 토큰 인증 (`src/web/routers/auth.py:61-92`):**
  계정 검증을 통과한 유저에게 별도 웹 회원가입 절차 없이 1회성 `magic_token`이 담긴 링크를 발급했다. 웹 백엔드는 토큰을 검증 및 즉시 소모(Consume)한 뒤 7일 유효기간의 `forum_session` JWT 쿠키(`HttpOnly`, `Secure`, `SameSite=Strict`)를 발급하여 `/guide`로 안전하게 연결했다.
- **이벤트 기반 역할 승급:**
  유저가 웹 가이드 서약을 완료(`POST /auth/complete`)하면 DB의 `is_guide_completed` 컬럼을 갱신하고, 앞서 구축해둔 Redis 이벤트 버스에 `onboarding:complete` 토픽을 발행했다. 봇 리스너가 이를 비동기 수신하여 해당 유저의 역할을 격리용 '뉴비'에서 정식 '멤버'로 즉시 승급했다.

---

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)

### 3.1. 3초 인터랙션 타임아웃 방어: `defer` 지연 응답
- **문제 상황:**
  해외 Mojang API 통신과 DB 쿼리가 겹치면서 디스코드의 3초 ACK 제한 시간을 초과하여 `Interaction failed` 오류가 발생하고 유저의 폼 제출이 무효화되는 현상이 발생했다.
- **해결책 (`onboarding_modal.py:39`):**
  모달의 `on_submit` 진입 즉시 `await interaction.response.defer(ephemeral=True)`를 실행하여 디스코드 게이트웨이로부터 최대 15분 유효한 응답 유예 토큰을 선제 획득했다. 이후 외부 통신과 DB 처리가 끝난 뒤 `interaction.followup.send()`로 최종 피드백을 전달하여 타임아웃을 차단했다.

### 3.2. 봇 인스턴스 HTTP 세션 재활용
- 매 요청마다 `aiohttp.ClientSession()`을 새로 생성하고 파기하는 방식은 잦은 핸드셰이크 오버헤드를 유발한다.
- 봇 프로세스가 유지하고 있는 전역 세션(`interaction.client.session`)을 재사용하여 TCP 연결을 재활용하고, 세션 참조가 유실된 예외 상황에서만 단발 세션으로 폴백(Fallback)하도록 구성했다 (`onboarding_modal.py:66-88`).

### 3.3. 외부 API 호출 제한 및 어뷰징 방어: Redis 브루트포스 락
- **문제 상황:**
  오탈자가 포함된 마인크래프트 계정명을 반복 입력할 경우 Mojang API의 Rate Limit(HTTP 429)이 발생하여 다른 정상 유저의 인증까지 마비될 위험이 있었다.
- **해결책 (`onboarding_modal.py:110-158`):**
  - Redis의 `INCR`와 `EXPIRE(3600)`를 활용하여 `rpgsync:fail:{user_id}` 키로 유저별 실패 횟수를 1시간 동안 추적했다.
  - 연속 3회 실패 시 모달 제출을 잠금(Lock) 처리하고, 스태프 관제 채널로 알림 Embed를 전송하여 어뷰징을 방지하고 스태프의 확인 명령어로만 잠금을 해제할 수 있도록 격리했다.

### 3.4. UUID 36자리 RFC 표준 정규화 (`format_uuid`)
- Mojang API가 반환하는 32자리 비정규화 문자열(`e06f...`)은 마인크래프트 Java 플러그인 및 PostgreSQL의 표준 36자리 UUID(`8-4-4-4-12`) 규격과 불일치했다.
- 플러그인이나 DB 조회 시 매번 문자열을 파싱하는 오버헤드를 없애기 위해, 수신 즉시 하이픈을 삽입하는 `format_uuid` 정규화 함수를 거쳐 DB에 적재했다. 또한 DB 컬럼에 `UNIQUE` 제약조건을 부여하여 타인의 마인크래프트 계정을 무단 도용하는 행위를 차단했다.

---

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)

- **디스코드 봇 계층:**
  - `src/bot/cogs/auth/onboarding_cmd.py`: `VerificationRequestView` (프라이빗 스레드 생성), `NicknameTriggerView` (모달 트리거 버튼), `onboarding:complete` Redis 리스너.
  - `src/bot/cogs/auth/onboarding_modal.py`: `UserNicknameVerificationModal` (`defer` 처리, Mojang API 조회, Redis 실패 락, `format_uuid`).
- **웹 백엔드 계층:**
  - `src/web/routers/auth.py`: `verify_magic_link` (매직 토큰 소모 및 JWT 쿠키 발급), `complete_guide` (`is_guide_completed` 갱신 및 Redis 이벤트 발행).
- **데이터베이스 계층:**
  - `src/database/auth.py`: `register_verified_user`, `update_guide_completion`, `is_guide_completed`.

---

## 5. 결과 및 엔지니어링 교훈 (Results & Lessons Learned)

1. **플랫폼 규격과 라이프사이클에 대한 이해:**
   디스코드와 같은 3rd-party 플랫폼 위에서 시스템을 구축할 때는 플랫폼이 강제하는 제약(3초 타임아웃, 유저 인터랙션 기반 모달 호출 제약)을 정확히 파악하고 그에 맞는 상태 전이(버튼 → 모달 → `defer` → followup)를 설계해야 한다.
2. **외부 의존성에 대한 방어적 태도:**
   외부 3rd-party API는 언제든 지연되거나 장애를 겪을 수 있으므로, 타임아웃 방어(`defer`), 커넥션 재사용, 캐시 기반 실패 횟수 제한(Rate Limit) 등의 회복탄력성 패턴이 필수적이다.
3. **비동기 이벤트 분리를 통한 시스템 안정성:**
   웹 위키에서의 서약 완료와 디스코드 봇의 역할 승급을 강결합하지 않고 Redis 이벤트 버스로 분리함으로써, 한쪽 시스템의 일시적 장애가 전체 온보딩 파이프라인의 중단으로 번지지 않도록 격리할 수 있었다.
