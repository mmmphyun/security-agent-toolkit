# Mini Watch · Day4 시작 자료

Day3 일반 서비스에는 로그인 성공 여부를 확인하는 코드만 있었다. Day4 시작 자료는 그 코드에 로그인 유지·로그아웃·글쓰기 접근 확인을 보완한 판이다.

감시 서비스에는 기존 요청 수집 API와 함께 운영자 인증·관찰 메모 API를 완성해 제공한다. Day4 본 수업에서는 이 API와 통신하는 React 화면을 만든다.

## 학생 시작 위치

- 저장소: https://github.com/zeroskill2400/mini-watch
- Day4 시작 자료: https://github.com/zeroskill2400/mini-watch/tree/day04-start
- 학생 폴더: `C:\work\mini-watch-day04`
- 기존 Day3 폴더는 보존한다. 새 폴더에서 Day4 시작 자료를 사용하고, PostgreSQL의 기존 `general_db`·`monitor_db`는 그대로 연결한다.

## 폴더별 준비

VS Code의 터미널 기본 프로필을 **Command Prompt**로 선택하고 새 터미널을 연다. 각 서비스 폴더에서 처음 한 번만 다음 순서로 실행한다.

일반 서비스:

```bat
cd C:\work\mini-watch-day04\general
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

감시 서비스는 새 터미널에서 준비한다.

```bat
cd C:\work\mini-watch-day04\monitor\backend
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

기존 venv를 준비했다면 `python -m venv venv`를 반복하지 않아도 된다. 실행할 때는 해당 폴더로 이동하고 `venv\Scripts\activate`를 실행한 다음 `python app.py`를 입력한다.

## 환경 설정

두 폴더 모두 `.env.example`을 복사해 `.env`를 만든다. 기존 PostgreSQL 접속 정보를 사용하며 `DB_NAME`은 각 파일에 적힌 이름을 유지한다.

일반 서비스 `general/.env.example`:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=general_db
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
SECRET_KEY=CHANGE_ME_TO_YOUR_OWN_RANDOM_SECRET
```

감시 서비스 `monitor/backend/.env.example`:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=monitor_db
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
SECRET_KEY=CHANGE_ME_TO_YOUR_OWN_RANDOM_SECRET
```

`DB_PASSWORD`에는 본인 PC의 PostgreSQL 비밀번호를 넣는다. 각 서비스 터미널에서 다음 명령을 실행해 서로 다른 `SECRET_KEY`를 만든다.

```bat
python -c "import secrets; print(secrets.token_hex(32))"
```

출력된 문자열을 해당 서비스 `.env`의 `SECRET_KEY=` 뒤에 붙인다. `.env`는 Git에서 제외하고, 키를 교안·스크린샷·채팅에 복사하지 않는다.

`SECRET_KEY`는 로그인 비밀번호와 별개로 세션 쿠키의 서명을 만들고 확인하는 서버 설정이다. 기존 .env를 사용하는 경우 DB 값을 바꾸지 말고 이 한 줄을 추가한다.

## SQL과 계정

일반 서비스가 실행 중이면 `Ctrl+C`로 멈춘다. pgAdmin에서 `general_db`의 Query Tool을 열고 **general/sql/day04.sql 전문**을 실행한다.

이 SQL은 기존 users·posts를 유지하며 글 번호가 기존 번호 뒤에서 이어지도록 시퀀스를 준비한다. 테이블 삭제나 게시글 초기화가 없다.

pgAdmin에서 `monitor_db`의 Query Tool을 열고 **monitor/backend/sql/day04.sql 전문**을 실행한다. 기존 http_events를 유지하고 users·notes를 추가한다.

각 서비스의 가상환경이 활성화된 터미널에서 실행한다.

```bat
python create_user.py
```

- 일반 서비스 공개 실습 계정: `student` / `Learn123!`
- 감시 서비스 공개 실습 계정: `operator` / `Learn123!`
- 같은 아이디가 있으면 비밀번호까지 그대로 유지한다. 이 경우 기존에 만든 계정의 비밀번호로 로그인한다.
- `create_user.py`는 이름·비밀번호를 묻지 않고 위 실습 계정을 만든다. 비밀번호 해시만 DB에 저장한다.
- 새 DB를 사용하는 경우에만 기존 create_database.sql로 `general_db` 또는 `monitor_db`를 먼저 만든다. 기존 수업 DB를 다시 만들지 않는다.

`notes`는 처음에 비어 있다. 목록·상세를 먼저 배우는 4교시에 예시 자료를 넣으려면 그 교시에서 소개한 `INSERT`를 한 번 실행하고, 이후 5교시에는 React 작성 폼으로 메모를 추가한다.

## 실행과 접속

감시 서비스 터미널과 일반 서비스 터미널에서 각각 실행한다.

```bat
python app.py
```

- 감시 서비스 확인: `http://127.0.0.1:5200/health`
- 예상 JSON: `{"service":"monitor","status":"ok"}`
- 일반 게시판: `http://127.0.0.1:5100/`
- 일반 로그인: `http://127.0.0.1:5100/login`
- 감시 React 화면은 1교시에서 만든 뒤 `http://127.0.0.1:5173`으로 접속한다.

일반 게시판은 비로그인 상태에서도 목록·상세를 읽을 수 있다. 새 글·수정·삭제 주소에 들어가면 먼저 로그인 화면으로 이동한다.

## 일반 서비스 보완 확인

1. 비로그인 상태에서 `/board/new`에 접속하면 `/login`으로 이동한다.
2. `student` 계정으로 로그인하면 목록 화면으로 이동하고 아이디·로그아웃 버튼이 보인다.
3. 글을 작성하고 새로고침해도 로그인 상태가 유지된다.
4. 로그아웃하면 새 글·수정·삭제 주소에서 다시 로그인을 요구한다.
5. 감시 React 운영자 로그인은 이 로그인과 별개다. 일반 서비스는 `general_session`, 감시 서비스는 `monitor_session` 쿠키를 쓴다.

`static/login.js`가 JSON으로 로그인 요청을 보내며 로그인 성공 후 목록 주소로 이동한다. 쿠키 저장·전송은 브라우저가 처리하고 서버가 쿠키의 서명을 검증한다.

Flask 기본 세션은 user_id·CSRF 토큰을 **서명한 쿠키**에 담는다. 서버의 별도 세션 DB에 저장하거나 내용을 암호화한 구현이 아니므로 비밀번호와 비밀 데이터는 세션에 넣지 않는다.

서버는 로그인 상태를 검사할 때 users 테이블에 그 사용자 번호가 남아 있는지도 확인한다. UI에서 쓰기 버튼을 숨기는 것만으로 접근을 제어하지 않는다.

## 제공 코드에서 새로 보이는 이름

- `session`: Flask가 요청 쿠키의 서명을 확인해 읽고, 변경 후 응답 쿠키로 다시 보내는 사용자별 값.
- `session.clear()`: 로그인 성공·로그아웃 때 이전 값을 비우는 메서드. 이후 필요한 user_id·새 CSRF 토큰을 채운다.
- `SECRET_KEY`: 쿠키 서명·검증에 쓰는 서버 비밀 설정.
- `current_user()`: session의 user_id로 현재 DB 사용자를 조회하는 함수.
- `csrf_token()`: 현재 세션에 변경 요청을 확인할 임의 문자열이 없으면 만들고 돌려주는 함수.
- `valid_csrf()`: 폼·요청 헤더의 문자열과 세션에 들어 있는 값을 비교하는 함수.
- `before_request`: 해당 Blueprint의 URL 함수를 실행하기 전에 공통 인증 검사를 실행하는 Flask 기능.
- `context_processor`: Jinja 템플릿에 login_user·csrf_token을 공통으로 전달하는 Flask 기능.
- `no_cache()`: 인증·메모 응답을 브라우저 캐시에 남기지 않도록 `Cache-Control: no-store`를 붙이는 함수.
- `error_handlers.py`: 잘못된 API 주소·요청 방법·DB 오류를 `{error: "안내"}` 형식으로 응답하는 모듈.

쿠키는 브라우저가 자동 전송하므로 변경 요청에는 별도로 CSRF 확인 값을 붙인다. React는 `/api/auth/me` 응답의 값을 받아 `X-CSRF-Token` 헤더에, Jinja 폼은 숨김 입력 칸에 넣는다.

## 감시 API 확인표

| 요청 | 비로그인 | 로그인 후 결과 |
|---|---:|---|
| GET /health | 200 | 서비스 상태 |
| GET /api/auth/me | 200 | user·csrf_token |
| POST /api/auth/login | CSRF 필요 | user·새 csrf_token |
| POST /api/auth/logout | CSRF 필요 | user:null·새 csrf_token |
| POST /api/events | 201 | 일반 서버에서 기록 수집 |
| GET /api/events | 401 | 최신 50건의 events |
| GET /api/notes | 401 | notes 목록 |
| GET /api/notes/번호 | 401 | note 한 건 또는 404 |
| POST /api/notes | 401 | CSRF 확인 후 note·201 |
| PUT /api/notes/번호 | 401 | CSRF 확인 후 note·200 |
| DELETE /api/notes/번호 | 401 | CSRF 확인 후 message·200 |

로그인 요청에 잘못된 아이디·비밀번호를 보내면 401, 제목·내용을 비우면 400, CSRF 값이 맞지 않으면 403, 없는 자료는 404다. 기존 `/auth/login` 경로도 일반 서비스에서 유지하며 이제 CSRF 확인과 세션 유지가 적용된다.

`POST /api/events`는 일반 서비스가 자기 요청 기록을 보내는 기존 수집 경로다. 운영자 브라우저 세션을 붙이지 않으며, 감시 서비스가 일반 서비스 로그인을 대신하는 구조가 아니다.

## 6교시 부록의 폴더 이동

부록 완성본(day05-start)에서는 일반 서비스 Python 파일이 `general/backend/`에 들어간다. 기존 일반 서비스 Python 파일·templates·static·sql을 이 폴더로 옮긴 구성이다.

`.env`와 `venv`는 배포물에 포함하지 않는다. 부록을 별도 폴더로 받은 학생은 `general/backend`에서 새 venv와 .env를 준비하고 동일한 `general_db`에 연결한다.

`db.py`는 자기 파일 옆의 `.env`를 읽으므로 새로운 배치에서도 `general/backend/.env`를 읽는다. 이전 Day3 폴더와 DB 데이터는 보존한다.

부록은 `routes/api_posts.py`를 추가해 `/api/posts` JSON CRUD를 제공한다. Jinja 화면은 `http://127.0.0.1:5100/`에서 비교할 수 있고, React 화면은 `http://127.0.0.1:5174`에서 본다.

두 화면은 같은 일반 backend와 general_db를 사용한다. React에서 추가한 글은 Jinja 목록에서도 확인할 수 있다.


## 학습 이력

try_*.py는 앞 수업의 연습 파일이다. 오늘 추가한 인증을 적용하기 전 요청 형식도 포함하므로 Day4의 실행 확인은 교안의 React 화면으로 진행한다.

## 다음 수업 시작 자료

https://github.com/zeroskill2400/mini-watch/tree/day05-start 에는 두 서비스의 React 화면까지 포함되어 있다. 본 브랜치는 그 출발점으로 frontend를 아직 만들지 않은 상태다.

---

## Mini Watch Day 4 과제 완성본 실행 가이드 및 구현 결과

### 1. 포트 구성 및 실행 주소
- **일반 서비스 (Flask)**: `http://127.0.0.1:5100`
- **감시 API (Flask)**: `http://127.0.0.1:5200`
- **감시 화면 (React + Vite)**: `http://127.0.0.1:5173` (Vite의 `/api` 프록시를 통해 5200 감시 백엔드로 전달)

### 2. 설치 및 실행 순서 (Windows CMD 기준)

#### Step 1: PostgreSQL DB 준비
```cmd
:: 1. PostgreSQL에 접속하여 general_db, monitor_db 생성
psql -U postgres -c "CREATE DATABASE general_db;"
psql -U postgres -c "CREATE DATABASE monitor_db;"

:: 2. 테이블 스키마 적용
psql -U postgres -d general_db -f C:\work\mini-watch-standalone\day04\general\sql\day04.sql
psql -U postgres -d monitor_db -f C:\work\mini-watch-standalone\day04\monitor\backend\sql\day04.sql
```

#### Step 2: 환경 설정 (.env)
- `general/.env.example` -> `general/.env` 복사 후 본인 DB 비밀번호 및 `SECRET_KEY` 설정
- `monitor/backend/.env.example` -> `monitor/backend/.env` 복사 후 본인 DB 비밀번호 및 `SECRET_KEY` 설정
- SECRET_KEY 생성: `python -c "import secrets; print(secrets.token_hex(32))"`

#### Step 3: 실습 계정 생성
```cmd
:: 일반 서비스 학생 계정 (student / Learn123!)
cd C:\work\mini-watch-standalone\day04\general
python create_user.py

:: 감시 서비스 운영자 계정 (operator / Learn123!)
cd C:\work\mini-watch-standalone\day04\monitor\backend
python create_user.py
```

#### Step 4: 서비스 실행 (터미널 3개 분리)
- **터미널 1 (일반 서비스)**:
  ```cmd
  cd C:\work\mini-watch-standalone\day04\general
  python app.py
  ```
- **터미널 2 (감시 백엔드 API)**:
  ```cmd
  cd C:\work\mini-watch-standalone\day04\monitor\backend
  python app.py
  ```
- **터미널 3 (감시 프론트엔드 React)**:
  ```cmd
  cd C:\work\mini-watch-standalone\day04\monitor\frontend
  npm install
  npm run dev
  ```

### 3. 구현된 기능 및 체크리스트 (전 항목 통과)

#### [필수 요구사항 20개 충족]
1. Flask 백엔드(5200)와 React 프론트엔드(5173) 실행 및 Vite 프록시(`/api`) 연결 완료.
2. PostgreSQL psycopg 연결 및 `%s` 파라미터 바인딩으로 SQL Injection 원천 방지.
3. 데이터 영속성: 메모 작성/수정 결과가 DB에 안전하게 보존되며 프로그램 재실행 후에도 유지.
4. 로그인 폼 상태: React State로 아이디/비밀번호를 관리하고 `POST /api/auth/login`으로 JSON 전송.
5. 계정 검증: Werkzeug `check_password_hash`를 이용한 비밀번호 해시 검증 (400 빈값, 401 불일치 처리).
6. 화면 전환: 로그인 성공 시 대시보드 표시, 로그아웃 시 사용자 State 초기화 및 로그인 폼 복귀.
7. 요청 기록 표시: 일반 서비스의 HTTP 메서드, 경로, 상태 코드를 뱃지와 함께 실시간 테이블로 표시.
8. 메모 목록 및 상세 조회: `GET /api/notes` 목록 표시(key=메모ID) 및 제목 클릭 시 `GET /api/notes/<id>` 상세 렌더링.
9. 메모 작성: `POST /api/notes`로 DB에 저장 후 목록 및 상세 뷰 동기화.
10. 메모 수정: 기존 내용을 폼에 채워 수정하며, 성공 시에만 DB 반영 및 취소 시 원래 내용 보존.
11. 메모 삭제: 삭제 확인 모달 대화상자를 거쳐 취소 시 보존, 확정 시에만 `DELETE /api/notes/<id>` 호출.
12. 최신 새로고침: 헤더의 '새로고침' 버튼으로 요청 기록과 관찰 메모 동시 재조회.
13. 유효성 검사: 공백/빈값 요청 시 서버 400 Bad Request 거절 및 클라이언트 에러 안내.
14. 404 처리: 존재하지 않거나 삭제된 메모 ID에 대해 서버 404 Not Found 및 UI 에러 뷰 렌더링.
15. 에러 피드백: 모든 API 실패 및 검증 실패 시 인라인 에러 알림(`role="alert"`) 제공.
16. 컴포넌트 분리: `src/components/` (LoginForm, Navbar, StatsCard, EventList, NoteList, NoteDetail, NoteForm, ConfirmModal).
17. API 모듈 분리: `src/api/` (client.js, auth.js, events.js, notes.js).
18. 백엔드 아키텍처 분리: `routes/`, `repositories/`, `db.py`, `auth_helpers.py` 유지.
19. 보안 및 환경 설정: `.env.example` 제공 및 실제 `.env` 파일 `.gitignore` 완벽 격리.
20. 재현성: 설치, 실행, DB 준비 방법 상세 문서화.

#### [심화 선택 기능 충족]
1. **요청 기록 검색 및 필터**: 경로 문자열 실시간 검색 및 응답 상태 코드(전체, 2xx, 3xx, 4xx, 5xx, 오류 전체) 드롭다운 필터 구현.
2. **요청 건수 요약 통계**: 상단 콕핏 카드에 전체 요청 수, 정상 요청 수(2xx/3xx), 오류 요청 수(≥400), 작성된 메모 수 실시간 집계 카드 제공.
3. **쿠키/세션 유지 및 API 보호**: `HttpOnly`, `SameSite=Lax` 세션 쿠키와 CSRF 토큰을 동기화하여 미로그인 상태의 API 직접 호출을 `401 Unauthorized`로 서버 레벨에서 원천 차단.

### 4. 자동 통합 테스트 스위트
- 검증 스크립트: `python test_day04_suite.py` 실행 시 13개 통합 검증 시나리오 전체 자동 검증 가능.
