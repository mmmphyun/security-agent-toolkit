# 미니프로젝트: 일반·감시 서비스 Docker Compose 분리 구성 및 격리 운영

본 문서는 일반 서비스(`m5d1-general`)와 감시 서비스(`m5d1-monitor`)를 독립된 두 개의 Docker Compose 스택으로 분리 구성하고, 내부 보안 격리망 및 외부 공유망(`m5d1-events`)을 통해 안전하게 상호작용하도록 구축한 실행 지침서입니다.

---

## 1. 프로젝트 개요 및 변경 내역

- **시작 코드 기준**: `mini-watch` `day06-start` 브랜치 소스 및 `day1-materials/project-starter` 템플릿
- **완성 및 직접 작성한 구성 파일**:
  - `compose-general.yaml`: 일반 서비스 스택 정의 (`general-db`, `general-api`, `general-gateway`)
  - `compose-monitor.yaml`: 감시 서비스 스택 정의 (`monitor-db`, `monitor-api`, `monitor-web`, `monitor-gateway`)
  - `gateways/general.conf`: 일반 Nginx Reverse Proxy 설정 (포트 8081 -> `general-api:5000`)
  - `gateways/monitor.conf`: 감시 Nginx Reverse Proxy 설정 (포트 8082 -> `monitor-api:5000`, `monitor-web:3000`)
  - `general/Dockerfile` & `monitor/backend/Dockerfile`: Python 3.13-slim 기반 Flask API 컨테이너 정의 (`0.0.0.0:5000`)
  - `monitor/next-frontend/Dockerfile`: Node.js 24 기반 Next.js 프로덕션 빌드/실행 환경 구성 (`0.0.0.0:3000`)
  - `general/sql/docker-init.sql` & `monitor/backend/sql/docker-init.sql`: 각 DB 컨테이너 최초 기동 시 자동 실행되는 테이블 및 초기 데이터 스크립트

---

## 2. 서비스 아키텍처 및 네트워크 토폴로지

### 2.1 아키텍처 다이어그램

```
[ 호스트 PC 브라우저 / 외부 ]
       │ :8081                     │ :8082
       ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ general-gateway  │        │ monitor-gateway  │
└────────┬─────────┘        └────┬─────────┬───┘
         │ (front-net)           │         │ (front-net)
         ▼                       ▼         ▼
┌──────────────────┐        ┌─────────┐ ┌───────────────┐
│   general-api    │        │monitor- │ │  monitor-web  │
│  (Flask :5000)   │        │   api   │ │(Next.js :3000)│
└─────┬──────┬─────┘        └────┬────┴─└───┬───────────┘
      │      │                   │          │
      │      │ (m5d1-events)     │          │
      │      └───────────────────┤          │
      │                          │          │
      ▼ (data-net)               ▼ (data-net)
┌──────────────────┐        ┌──────────────────┐
│    general-db    │        │    monitor-db    │
│ (PostgreSQL:5432)│        │ (PostgreSQL:5432)│
└──────────────────┘        └──────────────────┘
```

### 2.2 서비스별 네트워크 참여 및 공개 포트

| 서비스명 | 프로젝트명 | 참여 네트워크 | 호스트 공개 포트 | 역할 설명 |
| :--- | :--- | :--- | :--- | :--- |
| `general-gateway` | `m5d1-general` | `general-front-net` | `8081:80` | 일반 서비스 인그레스 프록시 |
| `general-api` | `m5d1-general` | `general-front-net`, `general-data-net`, `events-net` (`m5d1-events`) | 비공개 (내부 :5000) | 일반 비즈니스 로직 및 이벤트 송신 |
| `general-db` | `m5d1-general` | `general-data-net` | 비공개 (내부 :5432) | 일반 서비스 전용 PostgreSQL DB |
| `monitor-gateway` | `m5d1-monitor` | `monitor-front-net` | `8082:80` | 감시 서비스 인그레스 프록시 |
| `monitor-api` | `m5d1-monitor` | `monitor-front-net`, `monitor-data-net`, `events-net` (`m5d1-events`) | 비공개 (내부 :5000) | 감시 백엔드, 이벤트 수신, 메모 API |
| `monitor-web` | `m5d1-monitor` | `monitor-front-net` | 비공개 (내부 :3000) | 감시 Next.js 프론트엔드 대시보드 |
| `monitor-db` | `m5d1-monitor` | `monitor-data-net` | 비공개 (내부 :5432) | 감시 서비스 전용 PostgreSQL DB |

### 2.3 네트워크 별칭(내부 네트워크) vs 외부 공유망(`external: true`) 차이

- **Compose 내부 네트워크 (`general-front-net` 등)**:
  - Compose 파일 단위로 기본 네임스페이스 격리가 적용됩니다 (예: `m5d1-general_general-front-net`).
  - 동일한 네트워크 이름을 두 Compose 파일에 정의하더라도 별개의 브리지 네트워크가 생성되므로 스택 간 통신 및 DNS 해석이 차단됩니다.
- **외부 공유망 (`m5d1-events`, `external: true`)**:
  - Docker 엔진 레벨에서 사전에 생성된 단일 L2 가상 브리지 네트워크(`m5d1-events`)에 양쪽 스택의 컨테이너를 직접 바인딩합니다.
  - 이를 통해 `general-api`와 `monitor-api` 컨테이너만 동일 서브넷에 배치되어 Docker 내장 DNS(`127.0.0.11`)를 통해 상대방 컨테이너 이름(`http://monitor-api:5000/api/events`)으로 통신할 수 있습니다.
  - 두 DB 컨테이너(`general-db`, `monitor-db`)는 공유망에서 철저히 배제되어 외부/타 스택으로부터의 침해를 원천 차단합니다.

---

## 3. 실행 및 검증 가이드 (Step-by-Step)

### 3.1 사전 작업: 공유망 생성
```powershell
docker network create m5d1-events
```

### 3.2 이미지 빌드 및 감시 스택 기동
감시 API가 먼저 기동되어야 일반 서비스의 로그인 이벤트 수신 준비가 완료되므로, 감시 스택을 우선 실행합니다.

```powershell
# 감시 스택 빌드 및 백그라운드 기동
docker compose -f compose-monitor.yaml up -d --build

# 감시 API 헬스 확인 (HTTP 200 반환 대기)
curl -i http://localhost:8082/api/auth/me
```

### 3.3 일반 스택 기동
```powershell
# 일반 스택 빌드 및 백그라운드 기동
docker compose -f compose-general.yaml up -d --build
```

### 3.4 실습용 계정 생성
각 API 컨테이너에 접속하여 실습용 기본 계정을 프로비저닝합니다.
```powershell
# 일반 서비스 계정 생성 (student / Learn123!)
docker compose -f compose-general.yaml exec general-api python create_user.py student "Learn123!"

# 감시 서비스 계정 생성 (operator / Learn123!)
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py operator "Learn123!"
```

### 3.5 점검 및 상태 검증 명령어 명세

| 검증 단계 | 명령어 | 확인 목적 및 기대 결과 |
| :--- | :--- | :--- |
| **설정 문법 검증** | `docker compose -f compose-general.yaml config --quiet`<br>`docker compose -f compose-monitor.yaml config --quiet` | 각 YAML 파일의 문법적 오류 및 네트워크/볼륨 선언 정합성 검증 (출력 없음: 정상) |
| **컨테이너 실행 상태** | `docker compose -f compose-general.yaml ps`<br>`docker compose -f compose-monitor.yaml ps` | DB `healthy` 상태 여부, API/Gateway/Web의 `Up` 상태 및 포트 바인딩 확인 |
| **공유망 참여 검증** | `docker network inspect m5d1-events` | `m5d1-general-general-api-1`과 `m5d1-monitor-monitor-api-1` 두 컨테이너만 참여하고 DB는 제외되었는지 확인 |
| **컨테이너 간 이름 조회 (DNS)** | `docker compose -f compose-general.yaml exec general-api getent hosts monitor-api` | `general-api` 내부에서 `monitor-api`의 가상 IP 주소 해석 가능 여부 확인 |
| **앱 계층 응답 확인** | `curl -i http://localhost:8082/api/auth/me` | 네트워크 DNS 해석을 넘어 HTTP 웹 서버, 라우터, DB 세션 계층이 정상 동작하는지 확인 |

> **[이름 조회 vs 실제 앱 요청의 차이점]**
> - `getent hosts`: OS 및 Docker 데몬의 내장 DNS Resolver(L3/L4 수준)를 통해 도메인 이름이 IP로 변환되는지만 검증합니다.
> - HTTP API 요청: L7 애플리케이션 계층까지 패킷이 도달하여 Nginx 게이트웨이 리버스 프록시, Flask 라우터, PostgreSQL 세션/인증 메커니즘이 모두 정상 구동 중인지를 종합적으로 검증합니다.

---

## 4. 시나리오 동작 검증 절차

1. **일반 서비스 로그인 실패 및 성공 테스트**:
   - 브라우저에서 `http://localhost:8081/login` 접속.
   - `student` 계정에 잘못된 비밀번호를 입력하여 401 오류 발생 유발.
   - 정상 비밀번호(`Learn123!`)로 로그인하여 게시글 화면 정상 진입 (200 확인).
2. **감시 서비스 기록 및 메모 등록**:
   - `http://localhost:8082` 접속 후 `operator / Learn123!`로 로그인.
   - 요청 기록 탭에서 `login_failure` (401) 및 `login_success` (200) 이벤트가 수신되었는지 확인.
   - 메모 탭에서 제목 `Docker 점검`, 내용 `로그인 실패와 성공을 확인했다` 입력 및 등록.
3. **데이터 영속성 검증 (Graceful Down & Restart)**:
   - 볼륨 보존 종료 명령 실행:
     ```powershell
     docker compose -f compose-general.yaml down
     docker compose -f compose-monitor.yaml down
     ```
     *(주의: `-v` 플래그는 named volume을 파괴하므로 사용 금지)*
   - 감시 -> 일반 순서로 재실행:
     ```powershell
     docker compose -f compose-monitor.yaml up -d
     docker compose -f compose-general.yaml up -d
     ```
   - 재접속 후 기존 생성된 메모와 로그인 기록이 영구 보존되어 유지되는지 확인.

---

## 5. 심화 미션 해설

### 5.1 공유망 분리 및 복구 영향 분석
- **분리 명령**:
  ```powershell
  docker network disconnect m5d1-events m5d1-general-general-api-1
  ```
  - **영향**: `general-api` 컨테이너의 네트워크 네임스페이스에서 `m5d1-events` 인터페이스가 제거됩니다.
  - **결과**: `getent hosts monitor-api` 실행 시 DNS 해석 불가(`Host name lookup failure`)가 발생하며, 일반 서비스에서 발생하는 로그인 및 HTTP 요청 기록 전송 시 `requests.RequestException`이 발생하여 경고 로그가 기록되고 감시 서버로의 이벤트 전달이 전면 중단됩니다.
- **복구 명령**:
  ```powershell
  docker network connect m5d1-events m5d1-general-general-api-1
  ```
  - **결과**: `general-api`가 공유망에 재진입하여 정상적으로 `monitor-api`의 IP를 조회하고 기록 전송이 재개됩니다.

### 5.2 단순 재시작(`restart`)과 재빌드(`rebuild`)의 차이
- **원인 분석**:
  - `general/Dockerfile`과 `monitor/backend/Dockerfile`은 소스 코드를 `COPY . .` 명령을 통해 이미지 파일시스템 레이어에 정적으로 굽는 방식을 사용합니다.
  - `compose-*.yaml`에 호스트 경로를 컨테이너 내부로 바인딩하는 바인드 마운트(`volumes: - ./general:/app`)가 선언되어 있지 않습니다.
- **차이점**:
  - `docker compose restart`: 기존 컨테이너 프로세스만 재기동하므로 이미지 레이어에 구워진 과거 코드가 그대로 유지되어 소스 변경사항이 반영되지 않습니다.
  - `docker compose up -d --build`: 변경된 소스 코드를 바탕으로 Dockerfile의 빌드 레이어를 새로 생성한 뒤 컨테이너를 재생성하므로 코드 변경사항이 온전히 반영됩니다.

### 5.3 DB 격리망 구성과 다계층 검증의 필요성
- **조회 차이**:
  - `general-api`에서 `general-db` 조회: 동일 `general-data-net`에 속해 있으므로 정상적으로 IP(예: `172.26.0.2`)가 조회됩니다.
  - `general-api`에서 `monitor-db` 조회: `monitor-db`는 `monitor-data-net`에만 속해 있고 공유망 `m5d1-events`에 참여하지 않으므로 Docker DNS에서 이름을 찾지 못하고 조회가 실패합니다.
- **확인 단계 구분 이유**:
  1. **이름 조회 (DNS)**: L3/L4 네트워크 연결성 및 라우팅 가능 여부 확인
  2. **DB 인증 (Handshake & Auth)**: 포트 개방 여부, 계정명, 비밀번호, 접근 허용 정책(`pg_hba.conf`)의 일치 확인
  3. **SQL 실행 (Query Engine)**: 스키마, 테이블, 권한, 트랜잭션 등 데이터 계층의 논리적 무결성 확인
  이 세 단계는 네트워크, 인증, 스키마 계층의 결함을 격리하여 진단하기 위해 명확히 구분되어야 합니다.

### 5.4 Docker 설정 변경 PR 검토 및 병합 이력
- **개선 목적**: PostgreSQL 데이터베이스 컨테이너 종료 시 트랜잭션 플러시 및 WAL 체크포인트 기록 시간을 확보하여 비정상 종료로 인한 데이터 손상을 방지하기 위해 Graceful Shutdown 유예 시간(`stop_grace_period: 30s`)을 명시적으로 추가.
- **작업 브랜치**: `feature/docker-graceful-shutdown`
- **변경 파일**: `compose-general.yaml`, `compose-monitor.yaml`
- **커밋 식별자**: `d953325` (`refactor(docker): PostgreSQL DB 서비스에 정상 종료 유예 시간(stop_grace_period) 설정 추가`)
- **Pull Request**: [#1](https://github.com/mmmphyun/mini-watch/pull/1) (병합 커밋: `b73bc11`)

---

## 6. Git 커밋 이력 및 변경 내용

1. `6024744`: `feat(docker): 일반 및 감시 서비스 2-Compose 분리 구성 및 격리·공유 네트워크 연동`
   - 두 Compose 파일 명세 완성 (`compose-general.yaml`, `compose-monitor.yaml`)
   - DB `healthcheck` 및 의존성 `service_healthy` 체인 구성
   - Nginx 리버스 프록시 게이트웨이 및 호스트 공개 포트 분리 (`8081`, `8082`)
   - 외부 공유망 `m5d1-events` 설정 및 DB 네트워크 격리 구현
   - 세션 인증을 위한 `SECRET_KEY` 환경변수 설정 및 데이터 볼륨 영속화 보장
2. `d953325`: `refactor(docker): PostgreSQL DB 서비스에 정상 종료 유예 시간(stop_grace_period) 설정 추가`
   - 두 DB 서비스에 Graceful Shutdown 30초 유예 기간 설정
3. `b73bc11`: `Merge pull request #1 from mmmphyun/feature/docker-graceful-shutdown`
   - 작업 브랜치 검토 후 `main` 브랜치 병합 이력 반영
