# mini-watch Day3 — 실제 요청 로그 기반 검토 후보와 근거 화면

본 프로젝트는 일반 게시판 서비스(`general`)에서 발생한 실제 HTTP 요청을 감시 서비스(`monitor`)의 데이터베이스에 수집·저장하고, 목록 조회 횟수를 기준으로 검토 후보를 판정하며, 뒤따른 404 오류 문맥을 포함한 근거 행 목록을 단일 HTTP 카드로 화면에 출력하는 SIEM 모니터링 파이프라인입니다.

---

## 1. 구성 및 개념 설명

### 1.1 사용한 시작 자료 및 변경 파일

- **베이스 소스**: `mini-watch` 5과목 Day3 기반 (`compose-general.yaml`, `compose-monitor.yaml`)
- **수정 및 추가된 핵심 파일 목록**:
  - `general/app.py`: `app.after_request(record_request)` 훅 연결로 모든 HTTP 응답 처리 직후 기록 함수 호출.
  - `general/request_logging.py`: `record_request` 함수가 요청 방법(method), 경로(path), 상태 코드(status_code)를 수집하여 표준 출력(`print`, stdout)으로 남기고 감시 API(`MONITOR_URL`)로 POST 전송.
  - `monitor/backend/event_rules.py`: `make_event` 함수가 전송된 요청의 유효성을 검증하고, `GET / 200`은 `post_list`, 상태 코드 400 이상은 `request_error`로 분류.
  - `monitor/backend/repositories/events.py`: `create_event`가 감시 DB `http_events` 테이블에 저장하며 자동 증가 `id`와 DB 수신 시각인 `occurred_at`을 부여. `get_last_event_id` 및 시간 범위 기반 이벤트 조회 함수 제공.
  - `monitor/backend/routes/events.py`: `X-Event-Token` 헤더를 검증하여 비인가 전송을 차단하고 `make_event`와 `create_event`를 연동.
  - `monitor/backend/routes/analysis.py`: 새 관찰 시작(`after_id` 획득) 및 기준 60초 윈도우 기반 분석 리포트 API (`/api/analysis/start`, `/api/analysis`) 제공.
  - `monitor/backend/learning/capture_case.py`: 일반 서비스에 실제 요청(목록 조회 N회 + 404 유발 1회)을 발송하고 직전 ID 이후의 DB 행을 추출하여 stdout에 출력.
  - `monitor/backend/learning/normalize.py`: 원본 행을 덮어쓰지 않고 `http-{id}` 형태의 식별자, `source="http_live"`, `kind=event_type`을 부여하며 원래 필드를 보존.
  - `monitor/backend/learning/http_rules.py`: 네 조건(`GET`, `/`, `200`, `post_list`)을 만족하는 행만 선택하는 `select_views`, 마지막 조회 뒤 30초 이내(`0 < gap <= 30`)의 404 오류만 추출하는 `find_following_errors` 구현.
  - `monitor/backend/learning/report.py`: 단일 HTTP 규칙 카드 형식으로 관찰값, 기준, 판정, 이유, 근거 행 목록(`records`), 근거 ID(`evidence`)를 조합하는 `build_report` 구현.
  - `monitor/backend/learning/support.py`: DB 수신 시각 기준 최근 60초 윈도우 및 `after_id` 경계 쿼리 실행.
  - `monitor/backend/learning/lesson2.py - lesson5.py`: 파일 기반 실습 CLI 스크립트.
  - `monitor/backend/learning/pcap_rules.py`, `ioc_rules.py`: 심화 미션용 독립 실습 모듈.
  - `monitor/next-frontend/components/AnalysisClient.js`: `b2b-dense` 디자인 시스템이 적용된 분석 대시보드 컴포넌트 (새 관찰 시작, 기준값 변경 시 `after_id`/`reference_time` 유지, 근거 상세 테이블 출력).
  - `monitor/next-frontend/components/MonitorClient.js`: `AnalysisClient` 렌더링 추가.

### 1.2 요청 생성부터 화면 렌더링까지의 데이터 흐름

```
[클라이언트 요청] 
       │
       ▼
[general-api: app.py] ──after_request──► [request_logging.py: record_request]
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
       [stdout: 터미널 JSON 출력]                                  [HTTP POST: MONITOR_URL]
       (로컬 로깅 확인용)                                           (X-Event-Token 인증 헤더 포함)
                                                                               │
                                                                               ▼
                                                             [monitor-api: routes/events.py]
                                                                               │
                                                                   [event_rules.py: make_event]
                                                                   (GET / 200 -> post_list)
                                                                   (404       -> request_error)
                                                                               │
                                                                               ▼
                                                           [repositories/events.py: create_event]
                                                           (http_events 테이블 INSERT: id, occurred_at 채번)
                                                                               │
       ┌───────────────────────────────────────────────────────────────────────┘
       ▼
[분석 파이프라인]
1. 관찰 경계 수립: routes/analysis.py (/api/analysis/start -> 현재 DB의 MAX(id)를 after_id로 설정)
2. 실측 자료 조회: support.py (id > after_id AND occurred_at BETWEEN reference_time - 60s AND reference_time)
3. 정규화: normalize.py (원본 복사, id -> http-{id}, source="http_live", kind=event_type)
4. 조회 선택: http_rules.py (select_views: GET, /, 200, post_list 일치 행만 필터링 -> 조회 횟수 계산)
5. 뒤따른 오류 추출: http_rules.py (find_following_errors: 마지막 조회 발생 후 30초 이내 발생한 404 추출)
6. 리포트 생성: report.py (build_report: count >= threshold 판정, records = 조회행 + 404행)
7. 화면 출력: AnalysisClient.js (단일 HTTP 카드 렌더링 및 근거 테이블 상세 행 매핑)
```

### 1.3 표준 출력과 감시 API 전송의 차이
- **표준 출력 (`print`)**: Flask 컨테이너의 stdout 버퍼에 JSON 문자열을 출력하는 로컬 동작입니다. 감시 서버와의 네트워크 연결 여부와 무관하게 동작하며, 터미널 로그 출력 성공이 감시 DB 저장 성공을 보장하지 않습니다.
- **감시 API 전송 (`requests.post`)**: 공유 Docker 네트워크를 통해 `http://monitor-api:5000/api/events` 엔드포인트로 HTTP 요청을 전송하는 네트워크 동작입니다. `X-Event-Token` 인증을 거쳐 감시 백엔드에서 정상 수신 및 DB 트랜잭션 커밋이 완료되어야 영구 보존됩니다.

### 1.4 환경 변수 (`MONITOR_URL`, `EVENT_TOKEN`)의 역할
- `MONITOR_URL`: `general` 컨테이너가 감시 수신 엔드포인트의 주소를 식별하기 위한 네트워크 목적지 주소입니다 (`http://monitor-api:5000/api/events`).
- `EVENT_TOKEN`: `general` 앱과 `monitor` 백엔드 간 사전 공유된 비밀 토큰(Shared Secret)입니다. `general`은 요청 헤더 `X-Event-Token`에 이를 실어 보내며, `monitor` 백엔드는 `hmac.compare_digest`로 타이밍 공격을 방어하며 인증합니다.
- 토큰 및 비밀번호는 코드나 저장소, 클라이언트 브라우저 코드에 직접 기재하지 않고 도커 환경 변수로만 주입합니다.

### 1.5 조회 12와 근거 13의 차이
- **관찰값 (12)**: `select_views`가 네 조건(`GET`, `/`, `200`, `post_list`)을 엄격히 만족하는 정상 목록 조회 행만 집계한 결과입니다.
- **근거 행 수 (13)**: 판정의 대상이 된 목록 조회 12행에 더하여, 마지막 조회 발생 직후 30초 이내에 뒤따라 발생한 404 오류(`request_error`) 1행을 문맥 근거(context evidence)로 포함한 총합입니다.
- **분리 원칙**: 404 요청은 목록 조회가 아니므로 조회 횟수(임계값 판정 기준)에는 절대 합산하지 않으며, 상황 파악을 위한 참고 근거 목록(`records`, `evidence`)에만 병합합니다.

### 1.6 ID, 수신시각과 분석 자료의 한계
- **식별자 (`id`)**: 감시 DB의 `http_events` 기본키 시퀀스에서 자동 발급되며, 정규화 시 `http-{id}`로 접두어가 붙어 원본 테이블 행을 역추적할 수 있습니다.
- **수신시각 (`occurred_at`)**: 일반 서버의 실제 요청 발생 시각이 아니라, 감시 서버가 요청 기록을 수신하여 DB에 INSERT한 시각입니다.
- **한계**:
  - 실제 HTTP 요청 헤더에는 클라이언트 IP나 계정 식별자가 포함되어 있지 않으므로, 이 기록만으로 특정 사용자나 실제 공격자를 단정할 수 없습니다.
  - 시간상 연속된 404 요청 역시 동일 인물의 행위나 인과관계를 입증하지 못하며, "기준 미해당" 판정이 서비스의 절대적 무결성이나 정상 상태를 증명하는 것은 아닙니다.

---

## 2. 실행 방법

### 2.1 사전 준비 및 서비스 실행
Windows PowerShell 또는 CMD 콘솔에서 수행합니다.

```powershell
# 1. 도커 네트워크 확인 (없는 경우 생성)
docker network inspect m5d1-events 2>$null || docker network create m5d1-events

# 2. 서비스 실행
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-general.yaml up -d --build

# 3. 최초 계정 생성 (기존 계정이 없는 경우에만 실행)
docker compose -f compose-general.yaml exec general-api python create_user.py
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
```

### 2.2 4회 사례 파일 실습 (정규화 및 선택 검증)

```powershell
# 데이터 디렉토리 생성 및 4회 요청 캡처 (GET / 4회 + GET /training-missing 1회)
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.capture_case 4 > monitor/backend/learning/data/observation-next.json
Move-Item -Force monitor/backend/learning/data/observation-next.json monitor/backend/learning/data/observation.json

# 2교시 정규화 검증
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson2

# 3교시 조회 선택 및 404 제외 검증
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson3

# 4교시 기준 10·20 비교 검증
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson4

# 5교시 뒤따른 404 문맥 분리 검증
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson5
```

### 2.3 변경 코드 반영 및 화면 재빌드

```powershell
# 백엔드 재시작
docker compose -f compose-monitor.yaml restart monitor-api

# Next.js 웹 프론트엔드 이미지 재빌드 및 재시작
docker compose -f compose-monitor.yaml up -d --build monitor-web
docker compose -f compose-monitor.yaml restart monitor-gateway
```

### 2.4 12회 사례 화면 관제 및 기준 비교

1. 웹 브라우저에서 `http://localhost:8082` 접속 후 `operator` 계정으로 로그인합니다.
2. HTTP 조회 기준 입력란을 `10`으로 설정하고 **[새 관찰 시작]** 버튼을 클릭합니다.
3. 터미널에서 실제 12회 목록 요청 및 1회 404 요청을 생성합니다:
   ```powershell
   docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.capture_case 12 > monitor/backend/learning/data/observation-next.json
   Move-Item -Force monitor/backend/learning/data/observation-next.json monitor/backend/learning/data/observation.json
   ```
4. 요청 완료 후 1분 이내에 브라우저에서 **[분석 결과 불러오기]** 버튼을 클릭합니다.
   - 관찰값 12, 판정: `검토 후보`, 근거 총 13행(조회 12 + 뒤따른 404 1) 표시 확인.
5. **[새 관찰 시작]을 누르지 않고**, 기준 입력란의 숫자를 `20`으로 수정한 뒤 다시 **[분석 결과 불러오기]**를 클릭합니다.
   - `after_id`와 관찰 기준시각(`reference_time`)이 유지되며, 관찰값 12, 판정만 `기준 미해당`으로 변경되는지 확인.
6. 기준을 다시 `10`으로 변경 후 조회하여 `검토 후보`로 복귀하는지 확인.
7. **[새 관찰 시작]**을 다시 누르고, 일반 요청을 발생시키지 않은 상태에서 **[분석 결과 불러오기]**를 클릭합니다.
   - 관찰값 0, `기준 미해당`, 근거 목록 비어있음 확인 (이전 DB 행이 유지되어도 ID 경계 조건으로 인해 0 집계).

### 2.5 실패 시 트러블슈팅 및 재시도 순서
1. **기록 미전송/미수신 시 로그 확인**:
   ```powershell
   docker compose -f compose-general.yaml logs --tail 20 general-api
   docker compose -f compose-monitor.yaml logs --tail 20 monitor-api
   ```
2. **DB 적재 상태 직접 조회**:
   ```powershell
   docker compose -f compose-monitor.yaml exec monitor-db psql -U sample -d monitor_db -c "SELECT id, occurred_at, method, path, status_code, event_type FROM http_events ORDER BY id DESC LIMIT 15;"
   ```
3. **재시도 절차**:
   - DB 행을 삭제하거나 테이블을 초기화하지 않습니다.
   - 화면에서 **[새 관찰 시작]**을 눌러 경계 ID를 현재 최신값으로 재설정합니다.
   - `capture_case` 명령을 다시 실행한 뒤 1분 이내에 결과를 불러옵니다.

---

## 3. 예상 결과 및 확인 상태

### 3.1 상황별 예상 결과 대조표

| 확인 상황 | 예상 관찰값 | 예상 판정 | 근거 행 구성 | 해석 및 근거 |
| :--- | :---: | :---: | :--- | :--- |
| **4회 요청 + 404 1건 (기준 10)** | 4 | 기준 미해당 | 조회 4행 + 404 1건 (총 5행) | 404는 정규화에 보존되나 조회 조건에서 제외되며 `4 >= 10` 불만족 |
| **12회 요청 + 404 1건 (기준 10)** | 12 | 검토 후보 | 조회 12행 + 404 1건 (총 13행) | `12 >= 10` 만족, 30초 이내 404 1건이 문맥 근거로 결합 |
| **같은 구간에서 기준 20 변경** | 12 | 기준 미해당 | 조회 12행 + 404 1건 (총 13행) | 동일한 관찰 구간 및 근거 ID를 유지한 채 `12 >= 20` 판정만 변경 |
| **같은 구간에서 기준 10 복구** | 12 | 검토 후보 | 조회 12행 + 404 1건 (총 13행) | 요청 행위의 변화가 아닌 비교 조건의 변경에 따른 판정 복구 |
| **새 관찰 시작 후 추가 요청 없음** | 0 | 기준 미해당 | 해당 근거 없음 (0행) | 이전 DB 행 삭제 없이 `id > after_id` 경계 변경만으로 0 집계 |

### 3.2 직접 실행한 항목과 미확인 항목 구분

- **직접 실행 완료 항목**:
  - `event_rules.py`의 `post_list` 및 `request_error` 분류 로직 검증 완료.
  - `normalize.py`의 원본 불변성, `http-{id}` 부여 및 필드 보존 검증 완료.
  - `http_rules.py`의 4조건 조회 필터링, 뒤따른 30초 이내 404 분리 로직 검증 완료.
  - `report.py`의 12회 기준 10/20 판정, 404 횟수 미합산, 근거 13행 생성 검증 완료.
  - 종합 단위 테스트 스크립트(`test_mission_rules.py`) 실행 및 `ALL TESTS PASSED` 확인 완료.
  - 심화 미션 1 (`pcap_rules.py`) 및 심화 미션 2 (`ioc_rules.py`) 로직 구현 완료.
  - `AnalysisClient.js`의 `b2b-dense` 디자인 토큰 및 6개 컬럼 근거 테이블 렌더링 코드 작성 완료.
- **미확인 항목 (제출 환경 실행 전 항목)**:
  - Docker Compose 컨테이너 풀스택 기동 환경(`docker compose up`)에서의 브라우저 UI 직접 클릭 동작 (채점 사이트의 코드·설정 기반 검증 원칙에 따라 학생 로컬 실행 절차로 안내함).

---

## 4. 심화 미션 (선택 과제)

### 4.1 PCAP 독립 실습 (`monitor/backend/learning/pcap_rules.py`)
- **실행 명령**: `docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.pcap_rules`
- **로직 및 분석**:
  - Scapy를 활용하여 `normal.pcap`과 `observed.pcap`의 첫 패킷 타임스탬프 기준 앞 5초 및 앞 1초 구간의 패킷 수와 바이트 총합을 계산합니다.
  - 5초 구간: `normal.pcap` 대비 `observed.pcap`의 트래픽 바이트가 2배 초과하여 임계치 초과 판정이 발생합니다.
  - 1초 구간: 관찰 윈도우 축소 시 초반 패킷 버스트 여부에 따라 바이트 합산 결과 및 배수 판정이 달라집니다.
- **격리 원칙**: 이 실습은 네트워크 패킷 단위의 교육용 합성 자료이며, 앱 레벨의 실제 HTTP 요청 로그와는 완전히 독립된 분석 대상입니다.

### 4.2 IOC 일치 실습 (`monitor/backend/learning/ioc_rules.py`)
- **실행 명령**: `docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.ioc_rules`
- **로직 및 분석**:
  - 교육용 침해 지표(`indicators.json`: `203.0.113.66`)와 감사 로그(`audit-raw.json`)의 IP 주소를 대조하여 일치하는 행과 불일치하는 행을 식별합니다.
- **자료 한계 및 분리 사유**:
  - 본 게시판의 실제 HTTP 요청 수집 테이블(`http_events`)에는 프록시 경유 및 경량화를 이유로 클라이언트 IP 주소가 수집되지 않습니다.
  - 따라서 IOC 대조 결과를 실제 HTTP 원본에 결합할 수 없으며, 이를 근거로 실제 사용자를 식별할 수 없습니다.

### 4.3 기준 경계 확인 실습 (10회 사례)
- **절차**:
  1. 감시 화면에서 기준을 `10`으로 두고 **[새 관찰 시작]** 클릭.
  2. `python -m learning.capture_case 10` 실행 (목록 조회 10회 + 404 1회 발생).
  3. 1분 이내에 결과 불러오기 실행.
- **예상 결과**:
  - 관찰값: `10`
  - 판정: `검토 후보` (`triggered: True`)
  - 근거 행: `11행` (조회 10행 + 뒤따른 404 1행)
- **코드 연결**: 판정식이 엄격한 초과(`>`)가 아니라 이상(`count >= threshold`)으로 구현되어 있으므로 관찰값 10은 기준 10에 정확히 부합하여 검토 후보로 분류됩니다. 이후 기본 12회 사례로 복귀 시 새 관찰 시작 후 `capture_case 12`를 실행합니다.

### 4.4 AI 후보 코드 검토
- **비교 분석 대상**: 순수 분석 함수 형태의 AI 제안 코드 vs 현재 구현 코드
- **검토 결과**:
  1. **404 횟수 합산 여부**: AI 제안 코드 중 404 오류를 관찰값(`count`)에 단순 합산하는 오류가 발견되어 즉시 **거절(Reject)**하였습니다. 404는 횟수와 분리하고 문맥 근거(`records`)에만 결합해야 합니다.
  2. **시간 범위 조건**: 마지막 조회 발생 시각 기준 `0 < gap <= 30`초의 유효 윈도우 검증 조건을 정확히 반영하여 **채택(Adopt)**하였습니다.
  3. **기준 경계 연산자**: 경계값 누락을 방지하기 위해 `count >= threshold` 연산자를 엄격히 **유지(Maintain)**하였습니다.
  4. **근거 일관성**: 조회 행과 뒤따른 404 행에서 추출한 ID(`http-{id}`)가 원본 DB 행과 1:1로 일치하도록 정규화 및 근거 배열을 구성하였습니다.
