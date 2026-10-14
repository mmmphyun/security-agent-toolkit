# 실전 팀 프로젝트(CloudShield) 협업 거버넌스 및 Git 워크플로우 분석

> **[블로그 작성 지침 (자동화 파이프라인 참조용)]**
> 본 문서는 Day 05 블로그 포스팅 작성 시 단순 튜토리얼식 Git 기초 명령어(clone, add, commit) 나열을 배제하고, 실제 캡스톤 프로젝트([CloudShield / aleph-project](https://github.com/mmmphyun/aleph-project))에서 운영 중인 **프로덕션급 팀 협업 엔지니어링 거버넌스**를 핵심 의사결정 근거로 활용하기 위해 작성된 팩트 명세서입니다.

---

## 1. 프로젝트 개요 및 협업 배경

* **프로젝트명**: CloudShield (클라우드 하이브리드 위협 탐지·자동 대응 및 SecOps 파이프라인)
* **저장소**: [https://github.com/mmmphyun/aleph-project](https://github.com/mmmphyun/aleph-project)
* **협업 목적**: 웹/UI 구현 매몰을 방지하고, 클라우드 침해 위협 발생 시 10초 이내에 자동 탐지·격리·전파하는 분산 인프라 파이프라인(`공격 -> 타깃 EC2 -> CloudWatch Agent -> Lambda 오케스트레이터 -> L4 SG/L7 WAF/IAM 세션 차단 -> Slack 알림`)을 4인 팀이 병렬로 결함 없이 구축하기 위함.

---

## 2. 핵심 협업 아키텍처 및 거버넌스 규칙

### 2.1 도메인 엄격 분리와 역할 잠금 (Role-Lock)
팀원 간 포트폴리오 기여도 분쟁 및 코드 충돌을 원천 차단하기 위해 4대 직무 영역을 디렉터리 수준에서 물리적으로 격리했습니다:

1. **네트워크 (`network/`, `tests/unit/test_network.py`)**: 모의 공격 시뮬레이션(Hydra/Nmap), 트래픽 발생 스크립트, 패킷 분석 보고서.
2. **클라우드 B (`src/collector/`, `src/reporter/`)**: CloudWatch Agent 설정, 로그 집계, Slack Block Kit 알림 카드 전파 모듈.
3. **보안 (`src/detection/`)**: 정규식 기반 시그니처 탐지 룰, 침해사고 매퍼(Incident Mapper), 탐지 테스트.
4. **클라우드 A / 테크 리드 (`src/contracts/`, `src/remediation/`, `infra/`, `.github/`)**: 공통 데이터 인터페이스 계약, Lambda 오케스트레이터, Boto3 원자적 차단 엔진, Terraform IaC, OIDC CI/CD 파이프라인.

* **세션 락 (`.agent-role`)**: 로컬 환경의 `.agent-role` 파일 또는 프롬프트 선언을 통해 본인 담당 외 타 팀원 영역의 수정을 기계적으로 차단.
* **단일 소유권 매트릭스 (Single Ownership Matrix)**: `amazon-cloudwatch-agent.json`(클라우드 B), `nginx.conf`(클라우드 B), 격리 SG 규칙(네트워크), WAF IPSet 명세(보안) 등 경계선 파일의 단독 수정 권한을 명확히 정의.

### 2.2 보호된 데이터 계약 (Protected Contracts)
분산된 4개 모듈이 비동기로 통신할 때 인터페이스가 깨지는 사태를 방지하기 위해 데이터 모델을 동결 관리합니다:

* **불변 계약 경로**: `src/contracts/*.py` (IncidentReport, ThreatEvent, ActionPlan 등 Pydantic 모델)
* **계약 검증 테스트**: `tests/test_contracts.py`
* **규칙**: 테크 리드의 명시적 승인 없이 어떤 직무나 에이전트도 계약 파일을 임의 수정할 수 없으며, CI 파이프라인에서 계약 불변성 테스트를 강제 통과해야 합니다.

### 2.3 1인 1작업 WIP 제한 (WIP 1개 원칙) 및 PR Stacking 원천 차단
* 본인 직무의 미머지 열린 PR(`state:open`)이 1개라도 존재하는 경우, **신규 티켓 착수 및 GitHub Issue 생성을 하드 가드로 전면 금지**.
* 선행 PR이 main에 머지되기 전에 후속 작업을 브랜치로 쌓는 행위(PR Stacking)를 차단하여 Rebase 충돌 및 리뷰 병목을 제거.

### 2.4 직무 간 1:1 상호 짝꿍 리뷰 (Pair Review Matrix)
파이프라인 앞·뒤 단계의 담당자가 서로의 산출물을 검증하도록 순환 리뷰 체계를 구축했습니다:

| PR 발행 직무 (작성자) | 필수 1차 리뷰어 | 핵심 리뷰 관점 |
| :--- | :--- | :--- |
| **네트워크** | **보안** | 모의 공격 트래픽이 보안 시그니처 룰 탐지 조건에 부합하는지 검증 |
| **보안** | **클라우드 B** | 탐지 정규식이 CloudWatch Agent의 수집 로그 포맷과 일치하는지 검증 |
| **클라우드 B** | **네트워크** | 타깃 EC2 포트 및 Nginx 설정이 모의 공격 트래픽을 수용하는지 검증 |
| **전체** | **클라우드 A (테크 리드)** | 전역 파이프라인 거버넌스 및 계약 정합성 최종 스팟 체크 |

### 2.5 초경량 리뷰 표준 및 In-PR 피드백 원칙
* **태그 기반 2단계 분류**: 머지 블로커인 `[P1 - 필수]`와 개선 제안인 `[P2 - 권장]`으로만 분리, 지적 사항은 최대 2~3개 이내로 통제 (P1 없으면 즉시 Approve).
* **In-PR 반영 (이슈 증식 방지)**: 리뷰 피드백 수정 시 새 Issue를 열지 않고 동일 PR 브랜치에서 추가 커밋(`fix(<직무>): ...`)으로 해결.

### 2.6 노션 칸반 $\leftrightarrow$ GitHub Actions 단방향 동기화
* 작업자는 로컬 스크립트(`scripts/get_my_tasks.py`)로 노션의 `[시작 전]` 티켓을 읽기 전용으로 조회하고 Issue에 링크.
* 칸반 상태 전이(`[시작 전]` $\rightarrow$ `[진행 중]` $\rightarrow$ `[검토 중]` $\rightarrow$ `[완료]`)는 사람이나 에이전트가 직접 수정하지 않고, **GitHub Actions(`notion_sync.yml`)가 PR 라이프사이클 이벤트에 맞춰 100% 자동 전담**하여 동기화 불일치를 원천 차단.

### 2.7 단일 검증 게이트
* PR 발행 전 로컬 검증 스크립트(`powershell .\scripts\check.ps1`) 실행 필수:
  * Ruff 린트 및 포맷 검증 (`ruff check .`, `ruff format --check .`)
  * Pytest 단위 테스트 및 계약 무결성 검증 (`pytest tests/`)
  * 검증 실패 시 커밋/푸시 중단.

---

## 3. 엔지니어링 의사결정 요약 (포스트 매핑 포인트)

1. **단순 브랜치 분기 vs R&R 기반 Role-Lock**: 단순 Git 브랜치는 파일 단위 충돌을 방지하지 못하므로, 디렉터리 수준 R&R 분리와 계약(Contract) 동결을 통해 분산 개발 무결성을 확보함.
2. **무제한 PR 생성 vs WIP 1개 제한**: 다중 작업 병렬화로 인한 컨텍스트 스위칭과 리뷰 지연을 방지하기 위해 1인 1PR 엄격 제한을 도입함.
3. **자유 리뷰 vs 1:1 파이프라인 인접 직무 리뷰**: 기술적 연관성이 가장 높은 직전/직후 파이프라인 담당자가 1차 리뷰를 맡음으로써 결함을 조기 차단함.
