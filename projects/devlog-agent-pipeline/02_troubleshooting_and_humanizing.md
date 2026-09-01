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

### 결함 6: SSG 빌드와 클라이언트 렌더링 분리로 인한 Mermaid 런타임 에러 누락
- **증상:** 4일차 포스트의 다이어그램이 브라우저에서 깨져서 렌더링되지 않았으나, `npm run build`와 기존 하네스 검증을 정상 통과함.
- **원인:** Astro SSG 빌드는 HTML 태그만 생성하고 실제 SVG 렌더링은 브라우저의 `mermaid.render()`에서 비동기로 실행됨. 기존 하네스는 ```` ```mermaid ```` 문자열 존재 여부만 검사하여 엣지 라벨 괄호 미인용이나 `&` 다중 결합자 구문 오류를 사전에 감지하지 못함.
- **해결:** `pipeline/harness.py`의 `check_mermaid()`에 런타임 구문 파서를 탑재하여 특수문자 미인용, `&` 연결자, 괄호 쌍 불일치를 빌드 전 사전 차단하고 기존 포스트 다이어그램 전수 정비.

### 결함 7: 동일 발행일(pubDate)로 인한 블로그 아카이브 정렬 비결정성
- **증상:** 블로그 메인 및 아카이브 목록에서 일차별(Day 01 ~ Day 06) 순서가 무작위로 뒤섞여 렌더링됨.
- **원인:** 모든 포스트가 동일한 `pubDate`를 가지고 있어, JavaScript 정렬 엔진이 2차 기준 없이 파일 시스템의 무작위 파일 로드 순서대로 렌더링함.
- **해결:** `[...page].astro`에 `pubDate` 동일 시 `slug`를 기준으로 2차 정렬하는 멀티 키 정렬(`a.data.slug.localeCompare(b.data.slug)`)을 적용하고, 1~6일차 포스트의 `pubDate`를 실제 진행 일자로 순차 배정.

## 3. 한국어 휴머나이징 거버넌스 (`im-not-ai` 레포 내재화 및 하네스 Linter)
- **휴머나이징 내재화:** `im-not-ai` 기준의 72대 룰북을 `pipeline/rules/humanize_rules.md`로 레포 내에 포함시키고, `pipeline/harness.py`를 통해 이모지 완전 배제, 마크다운 헤더(`# `, `## `) 기반 필수 5대 섹션, Mermaid 다이어그램 문법, AI 상투어구를 결정론적으로 검증.
- **독립 리서치/Q&A 주석 승화:** 단순 실습 코드 라인별 고민 외에 작성자가 독립적으로 조사한 심층 보안 Q&A(Zero Trust, Dual LLM 패턴, Blast Radius 등)는 4번 섹션 `### 심층 방어 아키텍처` 독립 서브섹션 및 5번 회고 섹션으로 유기적 승화 배치.
- **괄호 영어 번역투 차단:** `손상(Broken)`, `부작용(Side-Effect)` 등 불필요한 번역투 괄호 영어를 차단하고, 공인 대문자 표준 약어(IDS, SOAR, SRP, CSV 등)만 선별 허용.
- **2중 검증 체계:** 마크다운 정적 하네스 검증(`harness.py`)과 Astro 프론트엔드 정적 빌드(`npm run build`)를 2중으로 통과해야만 초안이 확정되도록 파이프라인 구축.
