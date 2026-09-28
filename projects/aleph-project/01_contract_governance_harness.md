---
repo: "https://github.com/mmmphyun/aleph-project"
topic: "멀티 에이전트 협업 거버넌스와 Pydantic V2 Contract-First 스키마 동결"
tags: ["AgentGovernance", "PydanticV2", "ContractFirst", "GitHubActions", "DevSecOps", "CloudShield"]
---

# 프로젝트 제목: CloudShield — 멀티 에이전트 협업 거버넌스와 Contract-First 스키마 동결

## 1. 프로젝트 시작 배경 및 문제 정의 (Why)
- **에이전트 도입에 따른 컨텍스트 왜곡과 스키마 드리프트:** 팀원 전원이 Cursor, Claude Code 등 AI 코딩 에이전트를 도입하여 개발을 진행함에 따라, 에이전트가 타 팀원의 도메인 코드를 무단 수정하거나 사전 합의되지 않은 필드를 임의 추가하여 런타임 통합 실패를 유발할 위험이 컸다.
- **다직무 경계 분리와 물리적 하네스 필요성:** 클라우드 A/B, 보안 탐지, 네트워크 등 4대 직무 영역 간 인터페이스를 명확히 고정하고, 실제 AWS 배포 전 로컬에서 독립 개발 및 상호 검증이 가능한 컨트랙트 퍼스트 최소 실행 가능 하네스(MVH) 체계가 필수적이었다.

## 2. 주요 설계 의사결정 및 기술 스택 선정 (Architecture & Trade-offs)
- **Pydantic V2 기반 불변 데이터 계약 (`src/contracts/incident.py`):**
  - 탐지 엔진과 차단/알림 엔진 간의 전달 객체인 `IncidentReport`에 `frozen=True` 및 `extra="forbid"`를 적용하여 불변성을 보장하고 비인가 필드 주입을 원천 차단했다.
  - 가변 컬렉션(`list[str]`)의 참조 변조 취약점을 배제하기 위해 불변 시퀀스(`tuple[str, ...]`)로 인터페이스를 고정했다.
- **이벤트 인제스트 규격화 (`src/contracts/events.py`):**
  - CloudWatch Logs Subscription Filter가 전달하는 Gzip/Base64 압축 JSON 페이로드를 안전하게 역직렬화하고, `/var/log/auth.log` 원문에서 전통 BSD 및 최신 Ubuntu ISO 8601 타임스탬프를 동시 파싱하는 팩토리를 구축했다.
- **원격 CI 중심 단일 창구 집중 전략:**
  - Windows AppLocker 정책 및 PowerShell 환경 충돌 위험이 있는 로컬 Git pre-commit 훅 강제를 배제하고, GitHub Actions(`ci.yml`, `pr_title_lint.yml`, `labeler.yml`)를 단일 관문으로 설정하여 자동 라벨링과 컨트랙트 무결성을 기계적으로 검증했다.

## 3. 핵심 기술적 난관 및 트러블슈팅 (Challenges & Breakthroughs)
- **IP 유효성 검증 정규식 오버엔지니어링 제거:**
  - 초기 구현에서는 복잡한 정규식과 `ipaddress.IPv4Address`를 2중으로 호출하여 파싱 오버헤드가 발생했다.
  - 정규식을 완전히 제거하고 파이썬 표준 라이브러리 `ipaddress.IPv4Address` 단일 호출로 통합하여 옥텟 유효성과 비정상 문자열을 단일 경로로 검증했다.
- **ISO 8601 타임스탬프 무음 누락(Silent Drop) 방어:**
  - 전통적인 BSD 포맷(`Sep 03 14:20:01`)만 허용하던 초기 파서로 인해 최신 배포판 로그가 유입될 경우 파싱 예외로 이벤트가 누락되는 결함을 확인하고 정규식을 확장 반영했다.
- **R&R Scope Guard (`scripts/verify_rnr_scope.py`):**
  - `.agent-role`에 바인딩된 직무 외 타 디렉토리 수정을 정적으로 차단하는 린터를 구축하여 에이전트 간 코드 충돌을 원천 방어했다.

## 4. 인제스터 탐색 힌트 (Key Modules & Functions)
- **핵심 파일:** `src/contracts/incident.py`, `src/contracts/events.py`, `scripts/verify_rnr_scope.py`, `.github/workflows/ci.yml`
- **주요 클래스/함수:** `IncidentReport`, `SyslogAuthEvent`, `CloudWatchLogsPayload.from_subscription_filter`, `verify_rnr_scope`

## 5. 결과 및 회고 (Results & Lessons Learned)
- **성과:** 4개 직무 영역이 2주간 병렬 개발을 진행하는 동안 단 한 건의 스키마 드리프트나 런타임 인터페이스 불일치 장애 없이 파이프라인 통합을 완결했다.
- **교훈:** 다자간 에이전트 협업 환경에서는 문서화된 규칙보다 타입 시스템(Pydantic V2)과 CI 하드 가드가 유일하게 신뢰할 수 있는 단일 진실 공급원(SSOT)임을 실증했다.
