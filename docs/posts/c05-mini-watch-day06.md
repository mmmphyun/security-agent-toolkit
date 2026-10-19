---
title: "서비스 스택 분리와 격리 네트워크 설계 — Docker Compose와 Nginx 인그레스 구성"
slug: "c05-mini-watch-day06"
description: "일반 업무 서비스와 관제 서비스를 2-Compose 스택으로 분리하고 외부 브리지 공유망과 Nginx 인그레스 게이트웨이로 보안 경계를 설계한 기록."
pubDate: "2026-03-24"
category: "자동 대응 SOAR"
tags: ["Docker", "Docker Compose", "Nginx", "PostgreSQL", "보안망분리", "인그레스"]
status: "published"
---

## 1. 개요 및 학습 개념 요약

단일 로컬 호스트에서 업무 웹 서비스와 보안 관제 서비스를 함께 구동하면 자원 경합과 네트워크 간섭이 일어난다.
모든 프로세스가 호스트 루프백(`127.0.0.1`) 주소 공간을 공유하면 특정 프로세스의 포트 충돌이 서비스 전체 장애로 번진다.

당일 실습은 1~5교시의 Docker Compose 기초를 바탕으로, 6교시 미니프로젝트 시작틀의 실행 환경을 컨테이너 스택으로 완성하는 종합 과제였다.
시작틀(`day1-materials/project-starter`)에는 각 프로젝트별 데이터베이스(`general-db`, `monitor-db`)만 최소한으로 정의되어 있었다.

이 미완성 뼈대에 일반 서비스와 관제 서비스 컨테이너를 직접 추가하고, Nginx 게이트웨이와 Docker 네트워크를 구성했다.
두 스택 간 통신을 위해 외부 공유망 `m5d1-events`를 바인딩하고 최종 시나리오 테스트를 통과하는 실행 환경을 완성했다.

> 컨테이너 환경 구성의 핵심은 요구사항에 맞춰 서비스 네트워크를 격리하고, 통신이 필요한 지점에만 최소한의 공유 경로를 열어주는 것이다.

## 2. 전체 산출물 구조 및 진단/파이프라인 체계

전체 시스템은 호스트 포트 접근을 통제하는 게이트웨이, 업무 로직을 수행하는 API, 대시보드 화면을 렌더링하는 프론트엔드, 영속 데이터를 보관하는 데이터베이스로 구성된다.
각 컨테이너의 네임스페이스와 네트워크 참여 범위는 실습 요구조건에 맞춰 분리했다.

| 서비스 식별자 | 프로젝트 스택 | 소속 네트워크 | 호스트 포트 | 컨테이너 역할 및 연결 제약 |
| :--- | :--- | :--- | :--- | :--- |
| `general-gateway` | `m5d1-general` | `general-front-net` | `8081:80` | 일반 서비스 인그레스 프록시 (호스트 단일 진입점) |
| `general-api` | `m5d1-general` | `general-front-net`, `general-data-net`, `events-net` | 비공개 (내부 :5000) | Flask 업무 로직 처리 및 관제 이벤트 송신 |
| `general-db` | `m5d1-general` | `general-data-net` | 비공개 (내부 :5432) | PostgreSQL 영속화 (공유망 접속 차단) |
| `monitor-gateway` | `m5d1-monitor` | `monitor-front-net` | `8082:80` | 관제 서비스 인그레스 프록시 (경로 분기 및 통제) |
| `monitor-api` | `m5d1-monitor` | `monitor-front-net`, `monitor-data-net`, `events-net` | 비공개 (내부 :5000) | Flask 관제 백엔드, 감사 로그 적재 및 메모 API |
| `monitor-web` | `m5d1-monitor` | `monitor-front-net` | 비공개 (내부 :3000) | Next.js 관제 대시보드 인터페이스 |
| `monitor-db` | `m5d1-monitor` | `monitor-data-net` | 비공개 (내부 :5432) | PostgreSQL 관제 감사 로그 및 관찰 메모 영속화 |

각 서비스는 호스트에 포트를 직접 노출하지 않고 내부 Docker 브리지 네트워크를 통해서만 상호 통신한다.
외부 클라이언트는 Nginx 게이트웨이의 `8081` 및 `8082` 포트로만 유입되며 백엔드와 데이터베이스의 내부 IP 구조는 호스트에 드러나지 않는다.

## 3. 기존 체계의 한계와 도전 과제: 미완성 시작틀과 런타임 결함

강의에서 제공된 6교시 시작틀은 각 프로젝트에 PostgreSQL 데이터베이스 서비스 하나만 정의된 상태였다.
Flask 애플리케이션과 프론트엔드 컨테이너가 빠져 있어 서비스 간 통신이나 감사 로그 수신 동작을 전혀 수행할 수 없었다.

또한 데이터베이스와 웹 애플리케이션을 동시에 기동할 때 커넥션 레이스 컨디션이 반복해서 나타났다.
PostgreSQL 소켓 수신 준비가 완료되기 전에 Flask 애플리케이션이 연결을 시도하면서 초기화 실패로 프로세스가 즉시 종료되었다.

단순 실행 명령으로는 변경된 소스코드가 반영되지 않는 이미지 레이어 캐시 문제도 존재했다.
비동기 큐가 없는 로컬 실습 환경 특성상 관제 API가 늦게 뜨면 일반 서비스에서 보낸 초기 로그인 이벤트가 그대로 유실되는 구조적 한계도 내포했다.

## 4. 엔지니어링 의사결정 및 리팩터링

### 4.1. 2-Compose 스택 분리와 외부 공유망 m5d1-events 연동

시작틀의 단일 DB 뼈대를 바탕으로 `compose-general.yaml`과 `compose-monitor.yaml` 두 파일에 API, 게이트웨이, 웹 서비스를 직접 추가했다.
두 스택 간 통신은 사전에 생성한 단일 Docker 브리지 네트워크인 `m5d1-events`를 통해서만 이루어지도록 설정했다.

일반 스택의 `general-api`와 관제 스택의 `monitor-api`만 해당 공유망에 연결했다.
양측 데이터베이스는 전용 내부망(`general-data-net`, `monitor-data-net`)에만 묶어 공유망을 통한 타 스택의 데이터베이스 접근을 차단했다.

```yaml
networks:
  general-front-net: {}
  general-data-net: {}
  events-net:
    external: true
    name: m5d1-events
```

외부 네트워크(`external: true`) 지시자를 선언하여 Docker Compose가 임의의 프로젝트 접두사를 붙여 독립된 새 네트워크를 생성하지 못하도록 고정했다.
그 결과 Docker 데몬의 내장 DNS Resolver(`127.0.0.11`)가 `events-net` 안에서만 `http://monitor-api:5000/api/events` 호스트명을 정상적으로 해석한다.

### 4.2. pg_isready 헬스체크와 stop_grace_period 유예 시간 설정

데이터베이스 컨테이너 프로세스가 떴다고 해서 곧바로 SQL 쿼리를 받을 수 있는 상태는 아니다.
단순 컨테이너 실행 여부만 확인하는 기본 `depends_on`으로는 PostgreSQL 소켓 바인딩 완료 시점을 보장하지 못해 API 기동 실패가 발생했다.

이 결함을 해결하기 위해 `pg_isready` 명령을 활용한 헬스체크 블록을 DB 서비스에 정의하고 API 서비스가 `condition: service_healthy`로 이를 대기하도록 연결했다.
더불어 데이터베이스 정상 종료 시 트랜잭션 플러시 시간을 확보하고자 `feature/docker-graceful-shutdown` 브랜치를 분기하여 `stop_grace_period: 30s`를 적용하고 PR #1(`d953325` -> `b73bc11`)로 병합했다.

```yaml
    healthcheck:
      test:
        - CMD-SHELL
        - pg_isready -U sample -d general_db
      interval: 3s
      timeout: 3s
      retries: 20
    stop_grace_period: 30s
```

`general-api` 서비스에서는 `depends_on`의 의존성 조건을 `condition: service_healthy`로 선언했다.
PostgreSQL 소켓 수신이 헬스체크를 통과하여 건강 상태로 전환된 후에만 백엔드 컨테이너가 초기화되도록 기동 순서를 보장했다.

### 4.3. Nginx 인그레스 게이트웨이 구성과 감사 로그 수신 경로 통제

각 컨테이너의 내부 포트(5000, 3000)를 호스트에 직접 열지 않고 Nginx 컨테이너를 단일 진입점으로 배치했다.
`gateways/general.conf` 설정을 통해 `8081` 포트로 유입되는 HTTP 트래픽을 내부 `general-api:5000`으로 프록시 패스하도록 구성했다.

관제 게이트웨이(`gateways/monitor.conf`)는 `8082` 포트를 점유하며 화면과 API 경로를 L7 수준에서 분기했다.
특히 외부 브라우저나 제3자가 감사 로그 수신 엔드포인트에 임의의 이벤트를 삽입하지 못하도록 HTTP 메서드를 제한했다.

```nginx
server {
    listen 80;
    location = /api/events {
        limit_except GET { deny all; }
        proxy_pass http://monitor-api:5000;
        proxy_set_header Host $http_host;
    }
    location /api/ {
        proxy_pass http://monitor-api:5000;
        proxy_set_header Host $http_host;
    }
    location / {
        proxy_pass http://monitor-web:3000;
        proxy_set_header Host $http_host;
    }
}
```

`location = /api/events` 블록에 `limit_except GET { deny all; }` 지시자를 적용했다.
관제 웹 대시보드가 로그를 조회하는 `GET` 요청은 게이트웨이를 통과하지만, 외부에서의 `POST` 감사 로그 삽입 요청은 Nginx에서 403 Forbidden으로 차단된다.
정상적인 감사 로그 `POST` 요청은 오직 내부 공유망(`m5d1-events`)을 통해 `general-api`에서 `monitor-api:5000`으로 직접 전송될 때만 처리된다.

### 4.4. 공유망 단절 실험과 컨테이너 재빌드 레이어 메커니즘 규명

테스트를 완료한 후 심화 요구사항에 따라 런타임 네트워크 장애와 Docker 이미지 레이어의 동작 방식을 직접 검증했다.
`docker network disconnect` 명령으로 `general-api`를 공유망에서 인위적으로 분리하여 장애 격리를 실증했다.

네트워크가 분리되자 DNS 조회 실패와 함께 로그 전송 시 `RequestException` 경고 로그가 기록되었으나, 일반 서비스 자체의 업무 처리는 중단 없이 유지되었다.
이후 `docker network connect` 명령으로 공유망에 재진입시키자 관제 API로의 이벤트 송신이 즉시 정상 복구되었다.

```powershell
docker network disconnect m5d1-events m5d1-general-general-api-1
docker compose -f compose-general.yaml exec general-api getent hosts monitor-api
```

또한 소스코드 수정 시 `docker compose restart` 명령이 유효하지 않은 원인을 규명했다.
호스트 디렉토리를 바인드 마운트하지 않고 Dockerfile의 `COPY . .` 지시자로 소스를 이미지 레이어에 구운 구조에서는 단순 프로세스 재기동으로 변경사항이 반영되지 않는다.

컨테이너 환경에서 코드 수정을 반영하려면 반드시 `docker compose up -d --build`로 이미지 빌드 레이어를 새로 갱신해야 한다는 런타임 특성을 확인했다.

## 5. 검증 및 회고

### 5.1. 4단계 다계층 네트워크 격리 검증과 영속화 확인

6교시 종합 과제의 테스트 완료 기준을 충족하기 위해 단계별 점검 프로토콜을 수행했다.
단순 컨테이너 기동 여부 확인을 넘어 DNS 해석, L7 프록시 응답, 데이터베이스 격리, 볼륨 영속성을 순차적으로 실증했다.

첫째, `general-api` 내부에서 `getent hosts monitor-api`를 실행하여 공유망 내 호스트명 IP 해석을 확인했다.
반면 타 스택 DB인 `monitor-db`에 대한 호스트 조회를 시도했을 때는 DNS 해석 실패가 반환되어 데이터망 격리를 실증했다.

둘째, 일반 서비스 브라우저 화면(`http://localhost:8081/login`)에서 `student` 계정으로 의도적인 비밀번호 오류를 발생시켜 HTTP 401 응답을 유발했다.
이후 정상 비밀번호로 로그인하여 200 응답을 받은 뒤, 관제 서비스(`http://localhost:8082`) 대시보드에서 `login_failure` 및 `login_success` 이벤트가 수신되었음을 확인했다.

셋째, 관제 메모 탭에서 점검 메모를 등록한 뒤 `docker compose down` 명령으로 컨테이너를 정상 종료했다.
Named Volume(`general-data`, `monitor-data`)을 보존한 상태에서 스택을 재기동했을 때 사용자 계정과 관제 메모 데이터가 유지됨을 확인했다.

### 5.2. 현실적 회고 및 교훈

실습 과제를 통과하기 위해 설정을 채워 넣는 과정에서 서비스 기동 순서의 중요성을 체감했다.
감시 스택이 준비되기 전에 일반 스택을 먼저 실행하면 로그인 실패 이벤트가 전송 도중 유실되는 현상이 발생했다.

현재 구현에는 실패한 요청을 나중에 재전송하는 작업 큐가 없기 때문에 인프라 기동 순서에 전적으로 의존하는 한계가 있었다.
호스트 소스 변경 시 단순 재시작으로는 코드가 갱신되지 않는 Dockerfile 레이어 구조를 직접 겪으며, 로컬 개발 환경과 배포 환경의 볼륨 마운트 전략 차이를 명확히 이해하게 되었다.
