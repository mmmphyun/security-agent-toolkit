# DevLog Agent Pipeline: 런타임 트러블슈팅 및 한국어 휴머나이징 거버넌스

## 1. 개요
블로그 자동화 파이프라인과 프론트엔드 정적 빌드 환경을 구축하는 과정에서 발생한 핵심 결함 해결 및 AI 번역투 제거 과정의 기록입니다.

## 2. 주요 기술 결함 및 외과적 해결

### 결함 1: Node.js 버전 불일치로 인한 Astro 6 배포 실패
- **증상:** GitHub Actions Pages 배포 워크플로우에서 `Node.js v20 is not supported by Astro! Please upgrade to >=22.12.0` 에러 발생.
- **원인:** 최신 Astro 6 엔진이 Node.js 22 LTS 이상을 필수로 요구함.
- **해결:** `.github/workflows/deploy-blog.yml`의 `setup-node` 스텝을 `node-version: 22`로 상향 조정하여 즉시 해결.

### 결함 2: Shiki 구문 강조와 Mermaid 다이어그램 렌더러 충돌
- **증상:** 마크다운 내의 Mermaid 코드 블록이 Astro Shiki 하이라이팅에 의해 HTML span 태그로 분해되어 브라우저에서 다이어그램 SVG로 변환되지 않고 깨짐.
- **원인:** Mermaid 라이브러리가 순수 텍스트 대신 Shiki가 감싼 HTML 엔티티를 파싱하려다 문법 에러 발생.
- **해결:** `PostLayout.astro`에서 Shiki 코드 블록의 `textContent`를 정제한 뒤, `mermaid.render()` 비동기 API를 직접 호출하여 다크 테마 SVG 컨테이너로 교체하는 커스텀 클라이언트 렌더러 구현.

### 결함 3: Setuptools Flat-Layout 다중 패키지 빌드 충돌
- **증상:** `pip install .` 실행 시 `Multiple top-level packages discovered in a flat-layout: ['blog', 'pipeline', 'agent_core']` 에러 발생.
- **해결:** `pyproject.toml`에 `[tool.setuptools.packages.find]` 설정을 추가하여 빌드 대상을 `pipeline*` 디렉토리로 명시적 한정.

### 결함 4: SPA 렌더링 한계 극복 및 커리큘럼 컨텍스트 로더 개발 (`context_loader.py`)
- **증상:** 커리큘럼 허브 웹페이지가 JavaScript SPA로 동작하여 단순 `requests`나 `curl`로는 빈 HTML 스켈레톤만 수집됨.
- **해결:** 원격 엔드포인트를 호출하여 메인 과목/일차 맵을 구축하고, 세부 하위 블록까지 재귀적으로 파싱하는 컨텍스트 로더(`pipeline/context_loader.py`)를 개발하여 CLI(`harness.py --fetch-curriculum`)로 통합. 특정 허브 식별자는 `.env` 환경변수로 격리하여 보안성 확보.

### 결함 5: 전역 Git Hook 간섭 방지 및 docs/posts 전용 선택적 물리 차단
- **증상:** 일반적인 pre-commit 훅은 파이프라인 개선이나 실습 코드 수정 커밋까지 무조건 차단하여 개발자 마찰을 유발함.
- **해결:** `git diff --cached`를 검사하여 `docs/posts/` 수정이 포함된 경우에만 일회성 토큰(`.user_confirmed`)을 요구하고, 일반 코드 커밋은 자유롭게 통과시키는 선택적 물리 차단 가드레일 확립.

## 3. 한국어 휴머나이징 거버넌스 (`im-not-ai` 레포 내재화 및 하네스 Linter)
- **휴머나이징 내재화:** `im-not-ai` 기준의 72대 룰북을 `pipeline/rules/humanize_rules.md`로 레포 내에 포함시키고, `pipeline/harness.py`를 통해 이모지 완전 배제, 마크다운 헤더(`# `, `## `) 기반 필수 5대 섹션, Mermaid 다이어그램 문법, AI 상투어구를 결정론적으로 검증.
- **괄호 영어 번역투 차단:** `손상(Broken)`, `부작용(Side-Effect)` 등 불필요한 번역투 괄호 영어를 차단하고, 공인 대문자 표준 약어(IDS, SOAR, SRP, CSV 등)만 선별 허용.
- **2중 검증 체계:** 마크다운 정적 하네스 검증(`harness.py`)과 Astro 프론트엔드 정적 빌드(`npm run build`)를 2중으로 통과해야만 초안이 확정되도록 파이프라인 구축.
