# DevLog Agent Pipeline: CI/CD 및 렌더링 트러블슈팅 기록

## 1. 개요
블로그 자동화 파이프라인과 프론트엔드 정적 빌드 환경을 구축하는 과정에서 발생한 핵심 런타임/빌드 결함과 외과적 해결 기록입니다.

## 2. 발생한 주요 이슈 및 해결 과정

### 이슈 1: Node.js 버전 불일치로 인한 Astro 6 배포 실패
- **증상:** GitHub Actions Pages 배포 워크플로우에서 `Node.js v20 is not supported by Astro! Please upgrade to >=22.12.0` 에러 발생.
- **원인:** 최신 Astro 6 엔진이 Node.js 22 LTS 이상을 필수로 요구함.
- **해결:** `.github/workflows/deploy-blog.yml`의 `setup-node` 스텝을 `node-version: 22`로 상향 조정하여 즉시 해결.

### 이슈 2: Shiki 구문 강조와 Mermaid 다이어그램 렌더러 충돌
- **증상:** 마크다운 내의 Mermaid 코드 블록이 Astro Shiki 하이라이팅에 의해 HTML span 태그로 분해되어 브라우저에서 다이어그램 SVG로 변환되지 않고 깨짐.
- **원인:** Mermaid 라이브러리가 순수 텍스트 대신 Shiki가 감싼 HTML 엔티티를 파싱하려다 문법 에러 발생.
- **해결:** `PostLayout.astro`에서 Shiki 코드 블록의 `textContent`를 정제한 뒤, `mermaid.render()` 비동기 API를 직접 호출하여 다크 테마 SVG 컨테이너로 교체하는 커스텀 클라이언트 렌더러 구현.

### 이슈 3: Setuptools Flat-Layout 다중 패키지 빌드 충돌
- **증상:** `pip install .` 실행 시 `Multiple top-level packages discovered in a flat-layout: ['blog', 'pipeline', 'agent_core']` 에러 발생.
- **해결:** `pyproject.toml`에 `[tool.setuptools.packages.find]` 설정을 추가하여 빌드 대상을 `pipeline*` 디렉토리로 명시적 한정.
