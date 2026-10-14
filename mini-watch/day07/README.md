# 미니프로젝트: 일반·감시 서비스 클라우드 배포 및 오류 수집 운영

> [!IMPORTANT]
> **배포 계획 및 상세 아키텍처 명세서**: 전체 배포 설정, Supabase 연동 명세, 프록시 라우터, Sentry 장애 분석 및 심화 과제에 대한 상세 내용은 [deployment-plan.md](file:///c:/work/mini-watch-standalone/deployment-plan.md)를 참조하십시오.

---

## 1. 프로젝트 개요 및 배포 상태

본 프로젝트는 기존 일반 서비스(`general`), 감시 백엔드(`monitor/backend`), 감시 프론트엔드(`monitor/next-frontend`)를 클라우드 환경(Render Docker Web Service)에 배포하고, 외부 관리형 데이터베이스(Supabase PostgreSQL) 및 오류 추적 시스템(Sentry)을 연동하여 무중단 운영 환경을 구축한 프로젝트입니다.

- **작업 및 배포 브랜치**: `day2-deploy`
- **시작 코드 기준**: `day06-submit` (Day1 일반·감시 2-Compose 완성본) 및 `day07-cloud-materials`(`starter`) 지원 파일
- **세 앱의 배포 설정 및 진행 상태**:

| 앱 구분 | 서비스명 | Root Directory | Dockerfile Path | Health Check Path | 런타임 서버 | 배포 상태 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **일반 앱** | `mini-general` | `general` | `./Dockerfile` | `/health` | Waitress WSGI (`0.0.0.0:$PORT`) | 미배포 (배포 구성 완료 / 로컬 검증 완료) |
| **감시 API** | `mini-monitor` | `monitor/backend` | `./Dockerfile` | `/health` | Waitress WSGI (`0.0.0.0:$PORT`) | 미배포 (배포 구성 완료 / 로컬 검증 완료) |
| **감시 화면** | `mini-web` | `monitor/next-frontend` | `./Dockerfile` | `/` | Next.js Node.js Server (`:3000`) | 미배포 (배포 구성 완료 / 로컬 검증 완료) |

> **로컬 실행과 클라우드 배포의 구분**:
> - 기존 `compose-general.yaml`, `compose-monitor.yaml`, `gateways/` 설정은 로컬 개발 및 격리 컨테이너 테스트용으로 그대로 유지됩니다.
> - 클라우드 배포 환경(Render)에서는 Nginx 게이트웨이를 거치지 않고 각 앱의 `Dockerfile`을 통해 독립적인 Docker Web Service로 직접 빌드·서빙됩니다.

---

## 2. 직접 변경한 파일 및 변경 목적

| 파일 경로 | 변경 목적 및 적용 내용 |
| :--- | :--- |
| [general/Dockerfile](file:///c:/work/mini-watch-standalone/general/Dockerfile) | Werkzeug 개발 서버 대신 Waitress WSGI 프로덕션 서빙 명령(`0.0.0.0:$PORT`) 적용 |
| [general/requirements.txt](file:///c:/work/mini-watch-standalone/general/requirements.txt) | 프로덕션 WSGI 서버(`waitress==3.0.2`) 및 Sentry SDK(`sentry-sdk[flask]==2.72.0`) 의존성 추가 |
| [general/db.py](file:///c:/work/mini-watch-standalone/general/db.py) | Supabase Session pooler 대응 6대 환경변수 매핑(`DB_SSLMODE=require`, timeout 10초) |
| [general/sql/deploy.sql](file:///c:/work/mini-watch-standalone/general/sql/deploy.sql) | 일반 DB(`users`, `posts`) 무중단 배포 DDL 작성 (`IF NOT EXISTS`, 시퀀스 보존) |
| [general/create_user.py](file:///c:/work/mini-watch-standalone/general/create_user.py) | 12자 이상 비밀번호 입력을 위한 대화형 프롬프트 및 PBKDF2 해시 저장 로직 적용 |
| [general/auth_helpers.py](file:///c:/work/mini-watch-standalone/general/auth_helpers.py) | 32자 이상 `SECRET_KEY` 검증 및 `SESSION_COOKIE_SECURE` 환경변수 연동 |
| [general/request_logging.py](file:///c:/work/mini-watch-standalone/general/request_logging.py) | 감시 서비스 통신 시 `X-Event-Token` 헤더 전송, `/health` 트래픽 수집 제외 |
| [general/observability.py](file:///c:/work/mini-watch-standalone/general/observability.py) | Sentry SDK 초기화 및 개인정보/비밀값 필터링 훅(`before_send`) 구성 |
| [general/app.py](file:///c:/work/mini-watch-standalone/general/app.py) | `/health` 엔드포인트 연동 및 `/api/sentry-test` 0 나누기 오류(`ZeroDivisionError`) 정상 응답 수정 |
| [general/.env.example](file:///c:/work/mini-watch-standalone/general/.env.example) | Supabase 5432, postgres, SSL require 및 환경변수 템플릿 표준화 (비밀값 배제) |
| [monitor/backend/Dockerfile](file:///c:/work/mini-watch-standalone/monitor/backend/Dockerfile) | 감시 백엔드 Waitress WSGI 프로덕션 서빙 명령(`0.0.0.0:$PORT`) 적용 |
| [monitor/backend/requirements.txt](file:///c:/work/mini-watch-standalone/monitor/backend/requirements.txt) | 프로덕션 WSGI 서버(`waitress`) 및 Sentry SDK(`sentry-sdk[flask]`) 의존성 추가 |
| [monitor/backend/db.py](file:///c:/work/mini-watch-standalone/monitor/backend/db.py) | Supabase Session pooler 대응 6대 환경변수 매핑(`DB_SSLMODE=require`) |
| [monitor/backend/sql/deploy.sql](file:///c:/work/mini-watch-standalone/monitor/backend/sql/deploy.sql) | 감시 DB(`users`, `http_events`, `notes`) 무중단 배포 DDL 작성 (`IF NOT EXISTS`) |
| [monitor/backend/create_user.py](file:///c:/work/mini-watch-standalone/monitor/backend/create_user.py) | 대화형 계정 생성 스크립트 적용 |
| [monitor/backend/auth_helpers.py](file:///c:/work/mini-watch-standalone/monitor/backend/auth_helpers.py) | `SECRET_KEY` 32자 검증 및 `SESSION_COOKIE_SECURE` 환경변수 연동 |
| [monitor/backend/routes/events.py](file:///c:/work/mini-watch-standalone/monitor/backend/routes/events.py) | `/health` 엔드포인트 유지, `X-Event-Token` HMAC 검증 및 로그인 성공/실패 이벤트 분류 |
| [monitor/backend/observability.py](file:///c:/work/mini-watch-standalone/monitor/backend/observability.py) | 감시 백엔드 Sentry SDK 초기화 및 민감정보 제외 파이프라인 구성 |
| [monitor/backend/app.py](file:///c:/work/mini-watch-standalone/monitor/backend/app.py) | Sentry 초기화 연동 및 `/api/sentry-test` 엔드포인트 구성 |
| [monitor/backend/.env.example](file:///c:/work/mini-watch-standalone/monitor/backend/.env.example) | 감시 DB 및 감시 서비스 환경변수 템플릿 표준화 (비밀값 배제) |
| [monitor/next-frontend/Dockerfile](file:///c:/work/mini-watch-standalone/monitor/next-frontend/Dockerfile) | Node.js 24 기반 프로덕션 빌드/실행 환경 구성 (`npm ci` -> `build` -> `start`) |
| [monitor/next-frontend/app/api/[...path]/route.js](file:///c:/work/mini-watch-standalone/monitor/next-frontend/app/api/[...path]/route.js) | Next.js 서버 Route Handler 프록시 구성 (`Cookie`, `X-CSRF-Token`, `Set-Cookie` 중계) |
| [monitor/next-frontend/.env.example](file:///c:/work/mini-watch-standalone/monitor/next-frontend/.env.example) | Next.js 서버용 `MONITOR_API_URL` 템플릿 명세 |
| [monitor/next-frontend/.gitignore](file:///c:/work/mini-watch-standalone/monitor/next-frontend/.gitignore) | `.env.example` 커밋 허용 규칙(`!.env.example`) 명시 |
| [deployment-plan.md](file:///c:/work/mini-watch-standalone/deployment-plan.md) | 세 앱의 클라우드 배포 계획서, 아키텍처 다이어그램 및 문제 해결 가이드 작성 |

---

## 3. 데이터베이스 대응 및 계정 준비 방법

- **일반 DB**: Supabase 독립 프로젝트 A (`general/sql/deploy.sql` 적용 -> `users`, `posts`)
- **감시 DB**: Supabase 독립 프로젝트 B (`monitor/backend/sql/deploy.sql` 적용 -> `users`, `http_events`, `notes`)
- **공통 연결 규격**:
  - `DB_HOST`: Supabase Session pooler 주소
  - `DB_PORT`: `5432`
  - `DB_NAME`: `postgres`
  - `DB_USER`: `postgres.[PROJECT-REF]`
  - `DB_SSLMODE`: `require`
- **계정 프로비저닝 (로컬 가상환경)**:
  각 서비스 디렉터리(`general/` 또는 `monitor/backend/`)에서 `.venv` 가상환경을 활성화한 후 `python create_user.py`를 실행하여 12자 이상의 안전한 비밀번호로 사용자 계정을 생성합니다.

---

## 4. 서비스 간 요청 흐름 및 주소 체계

1. **감시 화면 요청 흐름**:
   - 브라우저(`Dashboard.jsx`) → Next.js 서버 동일 오리진(`/api/...`) 요청
   - Route Handler(`app/api/[...path]/route.js`)가 `MONITOR_API_URL`을 통해 감시 Flask(`https://<MONITOR_HOST>/api/...`)로 프록시 포워딩
   - `Cookie`, `X-CSRF-Token` 헤더 전달 및 응답의 `Set-Cookie`를 브라우저로 릴레이
   - 감시 Flask가 Supabase 감시 DB를 조회/갱신 후 응답 반환
2. **일반 로그 파이프라인 흐름**:
   - 사용자 웹 요청 처리 후 일반 Flask의 `request_logging.py`가 백그라운드에서 감시 Flask의 `MONITOR_URL`(`https://<MONITOR_HOST>/api/events`)로 POST 요청 전송
   - `X-Event-Token` 헤더에 `EVENT_TOKEN`을 실어 전송
   - 감시 Flask의 `routes/events.py`에서 토큰 일치 여부를 HMAC 비교로 검증한 뒤, `login_success`(200), `login_failure`(401), `http_request`로 분류하여 감시 DB `http_events`에 영구 저장

---

## 5. 실습 오류 수정 내역 및 배포 절차

### 5.1 오류 수정 명세
- **수정 파일**: `general/app.py`
- **수정 함수**: `sentry_test()`
- **오류 원인**: `result = 1 / 0` 실행으로 인한 무조건적인 `ZeroDivisionError` 예외 발생 (HTTP 500 유발)
- **수정 내용**: 0 나누기 연산을 제거하고 `result = "ok"` 정상 JSON 응답(`{'result': result}`)을 반환하도록 수정함.
- **오류 재현 및 수정 커밋**:
  - 오류 재현 커밋: `974208e` (`feat(general): 실습 오류 재현을 위한 /api/sentry-test 엔드포인트 및 헬스체크 연동`)
  - 오류 수정 커밋: `f29ad66` (`fix(general): /api/sentry-test 나눗셈 오류 수정 및 정상 응답 처리`)

### 5.2 코드 수정 및 배포 확인 표준 절차
1. 로컬 환경에서 코드 수정 및 테스트 실행
2. Git 커밋 생성 및 원격 브랜치(`day2-deploy`)로 푸시
3. Render 대시보드에서 해당 커밋의 빌드 로그 및 롤링 배포 성공 확인
4. `/health` 헬스체크 엔드포인트를 통해 서버 프로세스 정상 기동 확인
5. 실제 비즈니스 기능(로그인, 게시글 등록, 감시 이벤트 수신) 정상 동작 확인
6. 실습 오류 점검 시 사용한 `ENABLE_SENTRY_TEST` 플래그는 점검 완료 후 반드시 `false`로 재설정하고 배포 커밋 갱신

---

## 6. 마이크로 커밋 이력 요약

본 작업은 `atomic-commits` 원칙에 따라 1-Task 1-Commit 단위로 분해되어 실행되었습니다:

1. `fef50c6` - `feat(deploy): 일반 및 감시 Flask Docker 배포 및 Waitress 런타임 설정`
2. `56d76a0` - `feat(deploy): 감시 Next.js Docker 배포 설정 및 API 프록시 라우터 구성`
3. `25d6c08` - `feat(db): Supabase Session pooler 연동 및 무중단 배포 DDL 스크립트 분리`
4. `20c62bb` - `feat(auth): 사용자 생성 스크립트 대화형 전환 및 세션 쿠키 보안 강화`
5. `76eca9b` - `feat(pipeline): 일반-감시 간 이벤트 전송 토큰 인증 및 .env.example 표준화`
6. `7f061a8` - `feat(observability): Sentry SDK 초기화 및 민감정보 마스킹 파이프라인 연동`
7. `974208e` - `feat(general): 실습 오류 재현을 위한 /api/sentry-test 엔드포인트 및 헬스체크 연동`
8. `f29ad66` - `fix(general): /api/sentry-test 나눗셈 오류 수정 및 정상 응답 처리`
