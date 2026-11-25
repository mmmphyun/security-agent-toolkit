---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "R&R 경계 침범 사고 이후 로컬·CI 하네스 보강과 크로스 플랫폼 빌드 결함 해결"
tags: ["Governance", "Harness", "PowerShell", "Packaging", "CI", "CloudShield"]
---

# 프로젝트 제목: CloudShield — R&R 스코프 가드와 크로스 플랫폼 하네스 진화

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **문서 규칙의 한계와 PR #45 경계 침범:** `AGENTS.md`에 직무별 폴더 분리 규칙을 적어두었지만, PR #45에서 클라우드 B 담당자가 플랫폼 영역인 `scripts/`를 수정한 코드가 리뷰어 자동 제거 설정과 맞물려 `main`에 그대로 머지되었다.
- **로컬 검증 스크립트와 패키징의 환경 차이:** 팀원들이 쓰는 Windows PowerShell 환경과 실제 배포 대상인 AWS Lambda Linux 환경이 달라, 테스트 실패가 `[성공]`으로 출력되거나 C-Extension 바이너리가 빠진 패키지가 만들어지는 문제가 반복되었다.
- **문서 수정 시 불필요한 전체 테스트 지연:** 마크다운 문서나 이미지 같은 정적 자산만 고쳐도 로컬과 CI에서 약 3분이 걸리는 전체 단위 테스트가 매번 실행되었다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **직무 경계 검증기 (`scripts/verify_rnr_scope.py`):**
  - 현상: 브랜치 이름만 믿거나 자연어 지침에 기대면 타 직무 영역 파일을 실수로 덮어쓰기 쉽다.
  - 원리: GitHub Actions에서는 PR 작성자 계정(`github.event.pull_request.user.login`)과 브랜치 접두사를 교차 대조하고, 로컬에서는 `.agent-role`과 `git merge-base` 기준으로 Staged·Untracked 파일까지 전수 검사해 허용 경로 밖 수정 시 즉시 종료 코드 `1`을 반환한다.
  - 추가 방어: `.env` 같은 시크릿 파일이 Staged 인덱스에 올라가면 `check_forbidden_secrets`로 커밋·CI 단계에서 차단했다.
- **로컬 도구의 Python 단일 런타임 통일:**
  - 기존 보조 스크립트가 GitHub Actions 러너에 맞춘 Node.js(`.js`)로 섞여 있어, 로컬에 Node.js가 없는 팀원이 Python으로 중복 구현하는 우회가 발생했다.
  - `.js` 스크립트를 제거하고 Python 표준 라이브러리(`urllib.request`, `json`, `subprocess`)만 쓰는 구조로 통일해 팀원 필수 도구를 `uv`와 `gh` 두 가지로 줄였다.
- **문서 전용 변경 판별기 (`scripts/is_docs_only.py`):**
  - `src/`, `tests/`, `infra/`, `scripts/`, `.github/`나 코드 확장자(`.py`, `.tf`, `.yaml` 등)가 하나라도 걸리면 전체 테스트를 강제 실행하고(Fail-Closed), 화이트리스트 확장자(`.md`, `.png`, `.html` 등)만 바뀐 경우에만 단위 테스트를 건너뛰어 문서 작업 속도를 높였다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **PowerShell이 외부 `.exe` 실패 종료 코드를 무시하던 문제 (ADR-0009):**
  - 현상: Windows에서 `scripts/check.ps1` 실행 중 Pytest가 실패했는데도 스크립트가 멈추지 않고 `[성공]`을 출력했다.
  - 원리: Linux Bash의 `set -e`는 서브프로세스가 0이 아닌 코드를 돌려주면 즉시 종료하지만, PowerShell의 `$ErrorActionPreference = "Stop"`은 내부 cmdlet 예외만 잡을 뿐 외부 PE 바이너리(`pytest.exe`, `ruff.exe`)의 종료 코드는 예외로 취급하지 않는다.
  - 해결: 모든 외부 명령 직후 `$LASTEXITCODE -ne 0` 검사를 넣어 즉시 종료하게 만들고, 정적 검증 테스트(`test_check_ps1_contains_exit_code_guards`)로 가드 누락을 감시했다.
- **`pip` 백트래킹으로 Pydantic v1 순수 파이썬 휠이 내려받아지던 문제:**
  - 현상: `scripts/package_lambda.py` 테스트에서 잘못된 타깃 플랫폼을 넘겼을 때 2단계 의존성 수집에서 멈추지 않고 다음 단계로 넘어갔다.
  - 원리: 1순위 `uv`는 잘못된 플랫폼을 즉시 거절했지만, fallback으로 호출된 `pip`은 컴파일된 C-Extension(`pydantic-core`) 휠을 찾지 못하자 과거 버전으로 역추적(Backtracking)해 순수 파이썬 패키지(`pydantic 1.10.26-py3-none-any.whl`)를 정상 다운로드했다.
  - 해결: 패키지 지정에 `"pydantic>=2.0"` 제약을 고정하고, `validate_linux_native_binaries`로 `pydantic_core` 디렉터리와 `.so` 파일 존재 여부를 직접 확인하도록 바꾸었다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `scripts/verify_rnr_scope.py`, `scripts/check.ps1`, `scripts/package_lambda.py`, `scripts/is_docs_only.py`, `docs/roles/cloud-a/2026-09-17-rnr-scope-guard-and-runtime-unification.md`, `docs/roles/cloud-a/2026-10-02-secops-harness-evolution-and-postmortem.md`, `docs/adr/0009-cross-platform-harness-exit-code-and-hermetic-packaging.md`
- **주요 클래스/함수:** `resolve_role`, `is_file_allowed`, `check_forbidden_secrets`, `fetch_linux_dependencies`, `validate_linux_native_binaries`, `build_lambda_bundle`, `get_changed_files`, `is_docs_only_file`, `evaluate_changes`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 4개 직무 병렬 협업 과정에서 타 직무 파일 침범, 시크릿 커밋, Windows 로컬 검증 오판을 코드와 CI 게이트로 차단했고, 217개 단위 테스트가 돌던 시점부터 최종 1,900여 개 테스트 규모까지 일관된 검증 흐름을 유지했다.
- **회고:** 문서로 적은 규칙은 실수나 환경 차이 앞에서 쉽게 무력화되므로, 실행 환경(Windows PowerShell vs Linux CI)의 실제 종료 코드와 패키지 해결 규칙까지 검증 스크립트 안에 명시적으로 고정해야 함을 확인했다.
