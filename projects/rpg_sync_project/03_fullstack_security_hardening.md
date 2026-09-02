---
repo: "https://github.com/mmmphyun/rpg_sync_project"
topic: "학부 보안 이론의 실전 적용과 풀스택 방어 아키텍처 하드닝 (Part 3)"
tags: ["Web-Security", "XSS", "CSRF", "Clickjacking", "HSTS", "FastAPI-Middleware", "DOMPurify", "Self-RedTeaming"]
---

# 프로젝트 회고 Part 3: 공격자의 시선으로 내 서비스를 찌르다 — 학부 보안 수업과 풀스택 하드닝

## 1. 보안 하드닝 배경: 이론과 라이브 서비스의 교차검증 (Why)

### 1.1. 학부 네트워크·웹 보안 수업과 셀프 레드티밍(Self Red-teaming)
프로젝트 개발 당시 학부 과정에서 네트워크 및 웹 보안 과목을 수강하고 있었다. 수업에서 다루는 공격 벡터(XSS, CSRF, Clickjacking, MIME Sniffing, SQL Injection, ReDoS 등)를 단순한 시험용 암기 지식으로 넘기지 않고, **"현재 내가 개발하여 라이브로 서비스 중인 웹과 봇에 이 공격이 통하는가?"**라는 의문을 품고 직접 대입해보며 취약점을 전수 점검했다.

### 1.2. 라이브 서비스 환경에서의 보안 목표
- **유저 인터랙션 영역의 무결성 확보:** 직업 리뷰, 자유 게시판, 팁/공략 등 유저 입력을 받는 영역에서 악성 스크립트 실행(Stored XSS) 및 인젝션 차단.
- **HTTP 레벨의 전방위 방어막 구축:** ASGI 미들웨어 계층에서 클릭재킹, 비정상 출처 요청(CSRF), 불필요한 브라우저 API 접근을 프로덕션 수준으로 통제.
- **운영/개발 환경 분리 및 시크릿 격리:** Supabase, Redis, Discord Token 등의 민감 자산이 외부에 노출되거나 개발 중 오염되지 않도록 관리.

---

## 2. 프론트엔드·템플릿 다계층 방어 (Front-end & Template Hardening)

### 2.1. Jinja2 템플릿 엔진의 서버 사이드 자동 이스케이프 (SSR Auto-escaping)
FastAPI 백엔드에서 초기 HTML 뼈대와 데이터를 서빙할 때 `Jinja2Templates`를 도입했다.
- **도입 목적:** 데이터 구조화 및 템플릿 상속(`base.html`)의 편의성뿐만 아니라, Jinja2의 **기본 자동 이스케이프(Default Auto-escaping)** 기능을 활용하여 서버 사이드 렌더링(SSR) 단계에서 전달되는 변수 내 악성 스크립트 문자열(`<, >, &, ", '`)이 HTML 태그로 해석되지 않도록 1차 방어선을 구축했다.

### 2.2. 클라이언트 사이드 정규식 기반 5대 특수문자 이스케이프 (`public/base.js`)
비동기 Fetch API로 데이터를 받아와 브라우저 단에서 자바스크립트로 DOM을 동적 렌더링할 때는 Jinja2의 보호 범위를 벗어난다. 이 클라이언트 사이드 XSS 벡터를 방어하기 위해 정규식 이스케이프 함수를 구현했다.

```javascript
// public/base.js:64
function escapeHTML(str) {
    if (!str) return "";
    return String(str).replace(/[&<>'"]/g, match => {
        const escapeMap = { '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' };
        return escapeMap[match];
    });
}
```
- **적용 범위:** 유저 닉네임, 리뷰 코멘트, 스킬 설명, 공지사항 제목 등 모든 동적 렌더링 영역(`public/main.js`, `public/index.js`, `public/board.js`)에 전수 적용하여 템플릿 리터럴 삽입 시의 XSS 위험을 제거했다.

### 2.3. 마크다운 렌더링과 DOMPurify 2차 소독 (`public/tips.js`)
유저가 줄바꿈과 마크다운 문법을 사용하는 팁/공략 게시판의 경우, 단순 텍스트 이스케이프만으로는 서식을 지원할 수 없는 딜레마가 있었다.
- **해결 (`public/tips.js:106`):** `marked.parse()`로 마크다운을 HTML로 변환한 직후, **`DOMPurify.sanitize()`**를 파이프라인으로 연결하여 안전한 태그만 통과시키고 악의적인 스크립트/이벤트 핸들러를 완벽히 소독(Sanitize)했다.

---

## 3. 백엔드 Pure ASGI 커스텀 보안 미들웨어 (`src/web/main.py`)

프레임워크 기본 설정에 의존하지 않고, Starlette ASGI 표준 기반의 **`SecurityMiddleware`**를 직접 구현하여 모든 HTTP 요청과 응답을 감시 및 제어했다.

### 3.1. 엄격한 도메인 경계 검사(Boundary Check)를 통한 CSRF 방어
- **단순 `startswith`의 허점:** 단순히 `origin.startswith("https://my-domain.com")`으로 검사할 경우, 공격자가 `https://my-domain.com.attacker.com`과 같은 유사 도메인을 생성하여 검증을 우회할 수 있다.
- **방어 로직 (`src/web/main.py:60-64`):**
  ```python
  def is_trusted(value: str):
      if not value: return False
      for allowed in self.allowed_origins:
          if value == allowed or value.startswith(f"{allowed}/"):
              return True
      return False
  ```
  `POST`, `PUT`, `DELETE` 등 상태 변경 요청 시 Origin과 Referer가 화이트리스트 도메인과 정확히 일치하거나 하위 경로(`/`)로 시작하는지 경계를 엄격히 검증하여 우회 공격을 차단했다.

### 3.2. 클릭재킹 및 보안 헤더 전면 주입
- **클릭재킹(Clickjacking) 차단:** `X-Frame-Options: DENY` 및 `Content-Security-Policy: frame-ancestors 'none'`을 주입하여 타 사이트의 `<iframe>` 내부에서 위키 페이지가 로드되는 것을 원천 차단.
- **MIME 스니핑 방어:** `X-Content-Type-Options: nosniff`로 브라우저가 파일 타입을 임의로 추론하여 실행하는 취약점 차단.
- **권한 최소화:** `Permissions-Policy: geolocation=(), microphone=(), camera=()`로 불필요한 하드웨어 권한 무력화.

### 3.3. 개발 환경을 배려한 HSTS 락아웃(Lockout) 방지
- `Strict-Transport-Security`를 무조건 적용할 경우, 로컬 개발 환경(`localhost`, `127.0.0.1`)에서 HTTPS 인증서 부재로 인해 브라우저 접근이 영구 차단(HSTS Lockout)되는 실무적 문제가 발생한다.
- **조건부 헤더 주입 (`src/web/main.py:89-91`):** 호스트명을 검사하여 `localhost` 및 `127.0.0.1`일 때는 HSTS 헤더를 제외하고, 프로덕션 배포 도메인에만 `max-age=31536000; includeSubDomains`를 주입하도록 세심하게 분기 처리했다.

### 3.4. DoS 방어 및 Rate Limiting
- `slowapi` (`src/web/limiter.py`) 기반의 Rate Limiter를 엔드포인트에 적용하여 반복적인 무차별 대입 및 서비스 거부(DoS) 공격을 완화했다.

---

## 4. 보안 거버넌스 및 안티패턴에 대한 회고

### 4.1. 시크릿 관리와 환경 격리
- Supabase Key, Redis Password, Discord Bot Token, JWT Secret 등 모든 민감 정보는 `.env`로 격리하고 소스코드 저장소 커밋에서 원천 배제.
- 로컬 개발 환경과 클라우드 운영 환경(GCP)의 데이터베이스를 분리하여 개발 테스트 중 운영 데이터 오염 및 무결성 훼손을 방지.

### 4.2. '모호함을 통한 보안(Security by Obscurity)' 안티패턴 탈피
- **과거의 의사결정:** 개발 초기에는 취약점을 수정한 커밋 메시지가 외부에 노출될 경우 공격자에게 힌트를 줄 수 있다는 불안감에 보안 패치 커밋을 일반 리팩터링이나 사소한 수정으로 위장했다.
- **현재의 시니어 관점 반성:** 
  - 코드가 공개된 오픈소스나 협업 환경에서 커밋을 숨기는 행위는 '모호함을 통한 보안(Security through Obscurity)'이라는 전형적인 안티패턴에 불과하다.
  - 히스토리 추적을 어렵게 만들고 동료 개발자의 코드 리뷰를 방해하는 부작용이 더 크다.
  - 현재는 **공격 벡터나 익스플로잇 코드는 노출하지 않되, 방어의 목적과 영향 범위를 명확히 기술하는 Git 커밋 컨벤션**을 정립하여 투명성과 보안성을 동시에 확보하고 있다.

---

## 5. Part 3 결론 및 교훈

1. **이론과 실무의 선순환:**
   학교 수업에서 배운 보안 이론을 방치하지 않고 내 프로젝트에 셀프 레드티밍 형태로 대입해본 경험은 개발자의 보안 감수성을 획기적으로 끌어올렸다.
2. **다계층 심층 방어(Defense in Depth):**
   프론트엔드의 `escapeHTML` & `DOMPurify`, 백엔드의 `Pure ASGI SecurityMiddleware`, 인프라의 `.env` 환경 격리까지, 단일 방어선이 뚫려도 다음 계층이 막아내는 심층 방어의 필요성을 체감했다.
3. **진정한 보안은 투명성에서 나온다:**
   취약점을 감추려 하기보다 명확한 코드와 안전한 설계(Secure by Design)로 시스템을 단단하게 만드는 것이 올바른 엔지니어링 방향임을 배웠다.
