*1교시. 안내 페이지와 계약서 서버를 한 번에 띄우기*


## 보통은 백엔드로 요청을 찌르고 프론트엔드에서 받아쓰지 않아?

실무에서는 제공해주신 교재 방식인 **Nginx 리버스 프록시(8080 단일 진입점)** 구조가 표준입니다. 프론트엔드(8080)에서 백엔드(8090)로 직접 요청을 보내는 방식도 사용되지만, 여러 보안 및 아키텍처적 한계 때문에 운영 환경에서는 단일 진입점(Reverse Proxy 또는 API Gateway)을 거치도록 설계합니다.

---

### 두 방식의 차이점

**1. 브라우저가 백엔드(8090)를 직접 호출하는 방식**

* **동작:** 브라우저가 `[http://127.0.0.1:8080](http://127.0.0.1:8080)`에서 웹페이지를 로드한 뒤, JavaScript(Fetch/Axios 등)로 `[http://127.0.0.1:8090/document](http://127.0.0.1:8090/document)`를 직접 찌릅니다.
* **CORS(Cross-Origin Resource Sharing) 문제:** 포트 번호가 다르면(8080과 8090) 브라우저가 다른 출처로 인식하여 CORS 정책에 의해 기본적으로 통신을 차단합니다. 이를 풀기 위해 백엔드 서버(Flask)에 CORS 허용 헤더 설정을 추가해야 합니다.
* **보안 취약점:** 내부 API 서버(Flask)의 포트를 공용 인터넷망에 그대로 노출해야 하므로 공격 표면이 넓어집니다.

**2. Nginx가 8080으로 받아서 내부 5000으로 넘기는 방식 (교재 방식)**

* **동작:** 브라우저는 오직 `8080` 포트의 Nginx만 바라보며, Nginx가 경로(`/document`)를 판별하여 내부 도커 네트워크(`contract:5000`)로 전달합니다.
* **단일 도메인/단일 포트:** 브라우저 입장에서는 정적 페이지와 API 응답이 동일한 출처(`127.0.0.1:8080`)에서 오므로 CORS 문제가 원천 차단됩니다.
* **보안 및 내부 은닉:** 백엔드 서버의 포트를 외부(호스트 OS)에 개방할 필요가 없습니다. 실무에서는 `contract`의 `ports: - "127.0.0.1:8090:5000"` 줄 자체를 제거하고 내부 포트 `5000`만 Nginx를 통해 통신하도록 격리합니다.
* **중앙 제어:** Nginx 한 곳에서 SSL/TLS(HTTPS) 인증서 처리, 로드 밸런싱, 트래픽 제한(Rate Limiting), 공통 인증 등을 처리할 수 있습니다.

교재에서 `8090` 포트를 매핑해 둔 이유는 실습자가 백엔드 서버가 제대로 떴는지 브라우저나 `curl`로 직접 테스트(디버깅)할 수 있게 열어둔 임시 통로이며, 실제 배포 시에는 Nginx 프록시 뒤로 완전히 숨기는 것이 정석입니다.


## docker-compose.yaml과 compose.yaml은 버전업으로 짧은 이름을 지원하게 된 것?

`compose.yaml`은 Docker Compose 사양(Compose Specification)이 표준화되면서 공식 권장(Canonical) 표준 파일명으로 지정된 이름입니다. 단순히 "짧은 이름을 추가 지원"한 수준을 넘어, 레거시 도구(Compose V1)와의 의존성을 끊고 표준 규격을 확립하는 과정에서 우선순위가 높은 기본 파일명으로 정립되었습니다.

---

### 주요 차이점 및 우선순위

Docker Compose CLI(V2)는 `-f` 옵션 없이 명령을 실행할 때 현재 디렉터리에서 다음 순서대로 설정 파일을 탐색합니다.

1. `compose.yaml` (표준 권장)
2. `compose.yml`
3. `docker-compose.yaml` (레거시 호환)
4. `docker-compose.yml` (레거시 호환)

둘 다 동일하게 인식되며 기능상 동작 차이는 없습니다. 다만 같은 디렉터리에 두 파일이 공존할 경우 `compose.yaml`이 우선권을 갖습니다.

---

### 명칭이 변경된 배경

* **Compose Specification 표준화:** 기존에는 Docker 엔진 전용 도구(Python 기반 `docker-compose`)에 종속된 설정 파일이었으나, 사양이 오픈소스로 독립 표준화(`compose-spec`)되면서 Docker라는 특정 벤더명을 뺀 범용 명칭인 `compose.yaml`을 기본으로 채택했습니다.
* **CLI V2 전환:** Python 기반의 구형 독립 실행 파일(`docker-compose`)에서 Docker CLI 플러그인 형태의 Go 언어 구현체(`docker compose`)로 전환되면서 표준 파일명이 적용되었습니다.
* **확장자 표준 준수:** YAML 공식 표준 권장 확장자인 `.yaml`을 기본 채택하되, 기존 사용량이 많던 `.yml` 및 `docker-compose` 접두사 파일들에 대해 하위 호환성을 보장하고 있습니다.

신규 프로젝트 작성 시에는 공식 권장안인 `compose.yaml` 사용이 권장되며, 기존의 `docker-compose.yaml` 또한 별도 마이그레이션 없이 그대로 동작합니다.


## rpg-sync 프로젝트 경험 : 이 프로젝트에서 리버스 프록시를 쓰지 않고 SSR로 구현했다고 봐야해? 아니면 cloudflare를 쓰면서 해당 엣지 서비스가 프록시 역할을 했다고 봐야해? 아니면 CORS를 열어두고 쓴거야?

### 결론 요약

1. **"리버스 프록시를 쓰지 않고 SSR로 구현했는가?"**: 
   - **절반만 사실**. VM 내부에 Nginx·Apache 같은 인-하우스 리버스 프록시 컨테이너를 두지 않고 Uvicorn이 직접 80 포트를 수신하는 구조는 맞으나, 외부 네트워크 관점에서는 프록시가 존재함. 화면 구성 방식은 Jinja2 기반 **SSR(Server-Side Rendering)**이 맞음.
2. **"Cloudflare를 쓰면서 해당 엣지 서비스가 프록시 역할을 했는가?"**: 
   - **정확히 사실**. Cloudflare 엣지 노드가 **L7 리버스 프록시(Reverse Proxy) 및 SSL Termination(HTTPS 오프로딩) 계층** 역할을 전담함.
3. **"CORS를 열어두고 쓴 것인가?"**: 
   - **사실 아님 (`*` 전면 개방 아님)**. 기본 구조가 SSR이므로 페이지 탐색은 Same-Origin 상에서 동작하며, API 보호용 `CORSMiddleware`는 환경변수 화이트리스트(`ALLOWED_ORIGINS`)로 엄격히 제한되어 있음.

---

### 1. Cloudflare 엣지의 L7 리버스 프록시 동작 구조

- **트래픽 인입 경로**:
  - 클라이언트 브라우저 -> `[HTTPS:443]` -> **Cloudflare Anycast 엣지 노드(L7 Reverse Proxy)** -> `[HTTP:80]` -> **GCP VM ([`docker-compose.yml:L8-L10`](file:///c:/work/rpg_sync_project/docker-compose.yml#L8-L10) Uvicorn:8000)**
- **SSL Termination**:
  - 오리진 VM(FastAPI)은 자체 SSL 인증서(Certbot 등)를 로드하지 않고 순수 HTTP(8000)로 수신하며, HTTPS 암호화/복호화는 Cloudflare 엣지에서 전담(오프로딩).
- **L4 소켓 IP 단일화와 L7 헤더 파싱 ([`src/web/limiter.py:L6-L12`](file:///c:/work/rpg_sync_project/src/web/limiter.py#L6-L12))**:
  - Cloudflare를 경유하면 VM OS 커널 수준의 TCP 소켓 연결(`request.client.host`)은 모두 Cloudflare 엣지 서버의 IP(예: `172.68.x.x`)로 단일화됨.
  - 기본 `get_remote_address`를 사용하면 전 세계 사용자가 동일 IP로 묶여 Rate Limiter에 의해 대규모 오탐 차단(DoS)이 발생하므로, L7 헤더인 `cf-connecting-ip`를 우선 추출하도록 구현됨.
- **오리진 직접 타격 차단**:
  - GCP VPC 방화벽 인바운드 규칙에서 Cloudflare 공식 CIDR 대역만 80 포트 인입을 허용하고, 오리진 공인 IP로 직접 인입되는 패킷은 커널 레벨에서 즉각 DROP 처리하여 IP 스푸핑을 차단함.

---

### 2. 인-하우스 리버스 프록시(Nginx) 부재 및 SSR 채택 이유

- **Nginx 미사용 근거 ([`docker-compose.yml:L4-L15`](file:///c:/work/rpg_sync_project/docker-compose.yml#L4-L15))**:
  - GCP Free Tier e2-micro(1GB vRAM, 0.25 vCPU) 단일 노드 환경.
  - 별도의 Nginx/Caddy 컨테이너를 상주시킬 경우 발생하는 고정 메모리 점유(Resident Set Size) 및 컨텍스트 스위칭 오버헤드를 제거하기 위해 Uvicorn을 호스트 `80:8000`에 직결함.
- **Jinja2 SSR 채택 근거 ([`src/web/main.py:L70-L95`](file:///c:/work/rpg_sync_project/src/web/main.py#L70-L95))**:
  - 초기 프로토타입의 클라이언트 사이드 렌더링(CSR, Vanilla JS `innerHTML`) 환경에서 발생하던 DOM XSS 취약점을 원천 제거하기 위해 서버 사이드 렌더링으로 전면 마이그레이션함.
  - Jinja2 템플릿 엔진의 Auto-escape 메커니즘을 통해 유저 입력 데이터 내 `<`, `>`, `&`, `"`, `'`를 서버 메모리 단계에서 직렬화 이스케이프하여 브라우저로 전송.

---

### 3. CORS 및 통신 보안 정책

- **SSR과 CORS의 관계**:
  - 브라우저 주소창 입력이나 링크 이동으로 페이지를 로드하는 SSR 방식은 브라우저의 최상위 네비게이션(Top-level Navigation)이므로 동일 출처 정책(SOP) 및 CORS 사전 요청(OPTIONS Preflight) 제어 대상이 아님.
- **`CORSMiddleware` 화이트리스트 제한 ([`src/web/main.py:L121-L128`](file:///c:/work/rpg_sync_project/src/web/main.py#L121-L128))**:
  ```python
  ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://rpg-sync-wiki.example.com").split(",")
  app.add_middleware(
      CORSMiddleware,
      allow_origins=ALLOWED_ORIGINS,
      allow_credentials=True,
      allow_methods=["GET", "POST"],
      allow_headers=["X-API-Key", "Content-Type"],
  )
  ```
  - 와일드카드(`*`)가 아닌 특정 도메인으로 엄격히 한정.
- **Pure ASGI CSRF 보호 ([`src/web/main.py:L31-L60`](file:///c:/work/rpg_sync_project/src/web/main.py#L31-L60))**:
  - 상태 변경 메서드(`POST`, `PUT`, `PATCH`, `DELETE`) 인입 시 `SecurityMiddleware`에서 HTTP `Origin` 및 `Referer` 헤더의 도메인 경계(`allowed/`)를 직접 검증하여 외부 공격 도메인(`.attacker.com`)의 비정상 요청을 HTTP 403으로 즉각 드롭함.