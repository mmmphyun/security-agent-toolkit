---
heroKpis:
  - label: "대응 리드타임 단축"
    value: "15m → 4.2s"
    sub: "CloudShield 2단계 자동 격리"
  - label: "대륙 간 지연 극복"
    value: "405ms → 16.2ms"
    sub: "96.0% 단축 · RTT 200ms 방어"
  - label: "메모리 노출 국소화"
    value: "선형 메모리 소거"
    sub: "TPM 2.0 · Rust zeroize"
  - label: "1,000 RPS 스파이크"
    value: "1.17ms 거절"
    sub: "Redis Lua 99.36% Fast-Fail"

techTiers:
  - tier: "Language & Backend"
    role: "주력 구현 및 트러블슈팅"
    stacks:
      - "Python 3.11+"
      - "FastAPI"
      - "asyncio"
      - "Pydantic v2"
      - "boto3"
      - "pytest"
      - "Discord.py"
    proof: "1GB RAM 단일 노드 OOM 차단 및 Pydantic v2 멀티 에이전트 데이터 계약 통제"
    links:
      - label: "CloudShield 아키텍처 시리즈"
        url: "/security-agent-toolkit/posts/proj-cloudshield-1/"
      - label: "RPG Sync 트러블슈팅 시리즈"
        url: "/security-agent-toolkit/posts/proj-rpg-1/"

  - tier: "Infrastructure, Cloud & DB"
    role: "아키텍처 이해 및 실무 연동"
    stacks:
      - "AWS (Lambda, DynamoDB, WAFv2)"
      - "Terraform"
      - "Docker"
      - "K3s / KEDA"
      - "PostgreSQL"
      - "Redis (Lua, Streams)"
    proof: "DynamoDB 락-프리 슬라이딩 윈도우 구현 및 Terraform 7단계 보안 게이트 구축"
    links:
      - label: "ru-beacon 고가용성 시리즈"
        url: "/security-agent-toolkit/posts/proj-rubeacon-1/"

  - tier: "Research & Spec-Driven"
    role: "보안 표준 및 위협 모델 검증"
    stacks:
      - "Rust (WebAssembly)"
      - "W3C WebAuthn Level 3 (PRF)"
      - "TPM 2.0"
      - "AES-256-GCM"
      - "HKDF-SHA256"
    proof: "W3C WebAuthn PRF·TPM 2.0 하드웨어 바인딩 및 Rust Wasm 메모리 격리 검증"
    links:
      - label: "PrfVault GitHub"
        url: "https://github.com/mmmphyun/PrfVault"

projects:
  - id: "aleph"
    index: "01"
    name: "CloudShield"
    subtitle: "AWS 이벤트 기반 보안 위협 탐지 및 자동 격리 파이프라인"
    domainSummary: "AWS 인프라(VPC, EC2, CloudTrail)에서 발생하는 대량 보안 로그를 실시간 수집하여, 무차별 대입 공격 및 권한 탈취 시도를 자동 격리하고 LLM으로 위협 리포트를 생성하는 서버리스 SOAR 파이프라인입니다."
    period: "2026.08 - 2026.11"
    scale: "4인 팀 캡스톤 (팀장)"
    contribution: "기여도 50%"
    repoUrl: "https://github.com/mmmphyun/aleph-project"
    blogLinks:
      - title: "아키텍처 시리즈 (전 5편)"
        url: "/security-agent-toolkit/posts/proj-cloudshield-1/"
    stack:
      - "Python 3.11"
      - "AWS (Lambda, DynamoDB, WAFv2, EC2)"
      - "Terraform"
      - "Pydantic v2"
      - "pytest (moto)"
    diagramLight: "/security-agent-toolkit/portfolio/diagrams/cloudshield-architecture-light.svg"
    diagramDark: "/security-agent-toolkit/portfolio/diagrams/cloudshield-architecture-dark.svg"
    kpis:
      - label: "대응 리드타임 단축"
        value: "15m → 4.2s"
        sub: "CloudShield 2단계 격리"
      - label: "5스레드 동시 경합"
        value: "쓰기 유실 배제"
        sub: "DynamoDB list_append 검증"
      - label: "IaC 보안 검증"
        value: "7개 도구 연동"
        sub: "Checkov · tfsec · Trivy"
    tasks:
      - id: "task-a"
        topicLabel: "176ms 세션 지연 단축"
        title: "176ms 세션 방어를 위한 락-프리 윈도우 집계"
        problem: "단일 SSH 무차별 대입 공격 세션이 176ms 만에 종료되는 환경에서, 공격 로그가 서버리스 분산 환경으로 순간 인입될 때 낙관적 락 충돌로 인한 쓰기 유실이 발생했습니다."
        solution:
          - "전통적 분산 락을 배제하고 DynamoDB list_append 원자적 추가로 지연시간을 36-121ms로 통제했습니다."
          - "직전·현재·직후 3-버킷을 ConsistentRead로 동시 질의하여 경계면 공격 탐지 누락을 방어했습니다."
        comparisonHeaders: ["검증 항목", "전통적 분산 락 방식", "채택된 락-프리 3-버킷 윈도우"]
        comparisonRows:
          - ["쓰기 동시성 제어", "분산 락 획득/대기 (지연 예산 초과)", "DynamoDB 원자적 list_append (락 배제)"]
          - ["5스레드 동시 경합", "쓰기 락 충돌 시 재시도 오버헤드 급증", "로그 유실 없는 원자적 저장 검증"]
          - ["파이프라인 처리 지연", "평균 500ms 이상 (재시도 누적)", "36 - 121ms 유지 (목표 대비 1% 수준)"]

      - id: "task-b"
        topicLabel: "IaC 7단계 보안 게이트"
        title: "Terraform 모듈화 및 7단계 IaC 보안 검증 게이트"
        problem: "다중 환경(dev/stage/prod) 확장 시 리소스 블록이 3N으로 비대해지고 수동 설정 드리프트가 발생할 위험이 있었습니다. 특히 의도적으로 취약하게 만든 공격 실습 인프라(Threat Lab)와 코어 인프라가 섞이면 정적 보안 스캐너에서 대량의 오탐 노이즈가 발생하는 한계가 있었습니다."
        solution:
          - "인프라를 core-engine과 threat-lab으로 물리 분리하고 for_each 메타 인자와 templatefile()을 결합해 리소스 정의를 N으로 단일화했습니다."
          - "Checkov, tfsec, Trivy, Semgrep 등 7개 도구를 GitHub Actions에 통합하고 인라인 스킵 사유를 코드화하여 비인가 변경을 자동 거부했습니다."
        comparisonHeaders: ["비교 항목", "환경별 단순 복제 방식 (일반적 한계)", "모듈화 및 7단계 게이트 (채택)"]
        comparisonRows:
          - ["환경별 리소스 선언", "환경별 블록 수동 복제 (3N 비례)", "for_each + templatefile() 단일 정의 (N)"]
          - ["상태 충돌 방어", "로컬 상태 파일 파편화 (충돌 위험)", "S3 원격 백엔드 + DynamoDB State Lock 강제"]
          - ["보안 스캔 오탐 제어", "파이프라인 상시 실패", "물리 격리 및 인라인 예외 코드화"]

  - id: "rpg-sync"
    index: "02"
    name: "RPG Sync System"
    subtitle: "이기종 플랫폼 간 상태 동기화 및 인게임 가이드 백엔드"
    domainSummary: "마인크래프트 게임 서버(PaperMC), 디스코드 커뮤니티 봇(Discord.py), 웹 가이드(FastAPI)로 파편화된 유저 신원·역할·위키 데이터를 실시간 동기화하고 자연어 질의응답을 제공하는 통합 백엔드 시스템입니다."
    period: "2026.04 - 2026.07"
    scale: "개인 프로젝트 (1인 단독 개발·실운영)"
    contribution: "기여도 100%"
    repoUrl: "https://github.com/mmmphyun/rpg_sync_project"
    blogLinks:
      - title: "트러블슈팅 시리즈 (전 3편)"
        url: "/security-agent-toolkit/posts/proj-rpg-1/"
    stack:
      - "Python 3.11"
      - "FastAPI"
      - "Discord.py"
      - "asyncio"
      - "PostgreSQL (Supabase)"
      - "Redis"
      - "Docker"
    diagramLight: "/security-agent-toolkit/portfolio/diagrams/rpg-sync-architecture-light.svg"
    diagramDark: "/security-agent-toolkit/portfolio/diagrams/rpg-sync-architecture-dark.svg"
    kpis:
      - label: "평균 응답 지연"
        value: "405ms → 16.18ms"
        sub: "96.0% 단축 · Fast Path 캐시 결합"
      - label: "메인 루프 지터"
        value: "206ms → 14.64ms"
        sub: "92.9% 억제 · 동기 I/O 풀 격리"
      - label: "소켓 단절 복구"
        value: "6/6건 전건 복구"
        sub: "@db_retry 자가 치유"
    tasks:
      - id: "task-a"
        topicLabel: "200ms DB 커넥션 복구"
        title: "대륙 간 200ms DB 커넥션 자가 치유 및 캐싱"
        problem: "미국 오리건 호스트와 서울 데이터베이스 간 물리적 왕복 지연(약 200ms)이 있었습니다. 커넥션을 꺼낼 때마다 수행하던 SELECT 1 사전 검증 쿼리로 인해 API 응답이 405.66ms까지 지연되었습니다. 또한 관리형 DB의 유휴 세션 강제 정리로 봇 프로세스가 비정상 종료되는 장애가 발생했습니다."
        solution:
          - "사전 검증 쿼리를 제거하고 OS 커널 TCP 파라미터(keepidle=30, keepintvl=10, keepcnt=5)로 유휴 소켓을 관리했습니다."
          - "자주 조회하는 메타데이터를 Redis에 예열하고, 소켓 단절 시 커넥션을 풀에서 영구 폐기(close=True) 후 1회 재수립하는 @db_retry 데코레이터를 구축했습니다."
        comparisonHeaders: ["단계", "개선 조치", "평균 응답 지연 (초당 처리량)"]
        comparisonRows:
          - ["개선 전", "매 요청마다 SELECT 1 사전 검증", "405.66ms (2.47 RPS)"]
          - ["1단계 개선", "사전 검증 제거 + OS TCP Keepalive", "243.41ms (4.11 RPS)"]
          - ["2단계 개선", "메타데이터 Redis 인메모리 예열", "16.18ms (61.78 RPS, 25배 증대)"]
          - ["3단계 자가 치유", "@db_retry 자동 커넥션 재생성", "소켓 강제 종료 6회 중 6/6건 전건 복구"]

      - id: "task-b"
        topicLabel: "1GB RAM 워커 풀 격리"
        title: "1GB RAM 비동기 루프 블로킹 분리 및 경량 분산 락"
        problem: "단일 스레드 asyncio 루프 안에서 동기식 데이터베이스 질의(psycopg2)가 메인 루프를 200ms 이상 점유했습니다. 이로 인해 웹소켓 하트비트 전송이 지연되어 디스코드 게이트웨이 세션이 끊어졌습니다."
        solution:
          - "메인 이벤트 루프와 200ms 지연 I/O를 물리 분리하기 위해 전용 스레드 풀(ThreadPoolExecutor, 최대 20개)을 두고 asyncio.to_thread로 작업을 위임했습니다."
          - "1GB RAM 제약에 맞춰 임계구역 대비 안전 마진을 둔 Redis SET NX EX 15 Safe TTL 단발성 락을 설계하여 중복 실행을 통제했습니다."
        comparisonHeaders: ["성능 및 신뢰성 지표", "단일 이벤트 루프 (개선 전)", "벌크헤드 격리 + Safe TTL (개선 후)"]
        comparisonRows:
          - ["웹소켓 하트비트 지터", "206.04ms", "14.64ms (92.9% 지터 억제)"]
          - ["10건 병렬 요청 처리 시간", "2.495초", "0.358초 (85.7% 처리 시간 단축)"]
          - ["20건 동시 요청 폭주", "동시 승인 시 레이스 컨디션 발생", "1건 선점 및 19건 즉시 차단 (전건 방어)"]

  - id: "prfvault"
    index: "03"
    name: "PrfVault"
    subtitle: "하드웨어 보안 키 기반 무상태 자격증명 아키텍처"
    domainSummary: "중앙 서버 침해와 마스터 비밀번호 탈취 위협을 제거하기 위해, W3C WebAuthn Level 3 prf 확장과 하드웨어 보안 칩(TPM 2.0)만으로 브라우저 Wasm 격리 메모리 내에서 암호화 키를 즉석 유도·소거하는 무상태 자격증명 보관소입니다."
    period: "2026.09 - 2026.10"
    scale: "개인 연구 (1인)"
    contribution: "기여도 100%"
    repoUrl: "https://github.com/mmmphyun/PrfVault"
    blogLinks:
      - title: "연구 시리즈 (전 3편)"
        url: "/security-agent-toolkit/posts/proj-prfvault-1/"
    stack:
      - "Rust (WebAssembly)"
      - "TypeScript"
      - "W3C WebAuthn Level 3 (PRF)"
      - "TPM 2.0 / Windows Hello"
      - "AES-256-GCM / HKDF-SHA256"
    diagramLight: "/security-agent-toolkit/portfolio/diagrams/prfvault-architecture-light.svg"
    diagramDark: "/security-agent-toolkit/portfolio/diagrams/prfvault-architecture-dark.svg"
    kpis:
      - label: "마스터 키 저장 배제"
        value: "TPM 2.0 직접 유도"
        sub: "서버 DB 및 영구 파일 저장 배제"
      - label: "메모리 노출 국소화"
        value: "선형 메모리 소거"
        sub: "Rust Wasm zeroize 물리 소거"
      - label: "암호화 단위 테스트"
        value: "17/17건 전건 통과"
        sub: "키 유도 및 AES 무결성 검증"
    tasks:
      - id: "task-a"
        topicLabel: "Wasm 메모리 물리 소거"
        title: "OS 레벨 하드웨어 엔클레이브 연동 및 Wasm 메모리 격리 소거"
        problem: "기존 클라우드 패스워드 매니저는 마스터 비밀번호나 중앙 서버가 침해되면 대규모 자격증명이 유출될 위험이 있습니다. 또한 브라우저에서 자바스크립트로 암호화를 수행하면 가비지 컬렉터 수거 지연으로 인해 평문 키가 프로세스 메모리에 잔류하는 구조적 한계가 있었습니다."
        solution:
          - "W3C WebAuthn Level 3 prf 확장으로 TPM 2.0 하드웨어 엔클레이브에서 암호화 키를 직접 유도하는 무서버 로컬 볼트를 구현했습니다."
          - "암·복호화 연산을 Rust WebAssembly 선형 메모리 안에서 실행하고, 직후 zeroize crate로 평문 키를 메모리에서 덮어써 잔류 위협을 차단했습니다."
        comparisonHeaders: ["검증 영역", "플랫폼 한계 및 위협", "엔지니어링 구현 및 검증 결과"]
        comparisonRows:
          - ["플랫폼 확장 차단", "webauthn.dll의 내장 TPM PRF 호출 거부", "네이티브 호스트 및 ncrypt.dll FFI 자동 폴백 파이프라인 수립"]
          - ["메모리 잔류 위협", "브라우저 가비지 컬렉터의 메모리 해제 지연", "복호화 직후 Rust zeroize 호출로 선형 메모리 물리 소거"]
          - ["단위 테스트 실증", "로컬 키 유도 및 암·복호화 파이프라인 무결성", "단위 테스트 17/17건 전건 통과"]

  - id: "ru-beacon"
    index: "04"
    name: "ru-beacon"
    subtitle: "1,000 RPS 스파이크 방어를 위한 2-Tier Redis Lua 및 KEDA 비동기 파이프라인"
    domainSummary: "대규모 인게임 선착순 보상 이벤트 시 발생하는 1,000 RPS 순간 스파이크 트래픽으로부터 게임 서버 메인 틱(50ms)과 RDB 커넥션 풀을 보호하기 위해 설계한 비동기 이벤트 파이프라인 및 K3s 오토스케일링 인프라입니다."
    period: "2026.09 - 현재"
    scale: "개인 아키텍처 연구 (1인)"
    contribution: "기여도 100%"
    repoUrl: "https://github.com/mmmphyun/ru-beacon"
    blogLinks:
      - title: "고가용성 아키텍처 시리즈 (전 4편)"
        url: "/security-agent-toolkit/posts/proj-rubeacon-1/"
    stack:
      - "Java 21 (PaperMC API)"
      - "Spring Boot"
      - "Redis (Lua Script, Streams)"
      - "PostgreSQL (HikariCP)"
      - "K3s"
      - "KEDA"
      - "k6"
    diagramLight: "/security-agent-toolkit/portfolio/diagrams/rubeacon-architecture-light.svg"
    diagramDark: "/security-agent-toolkit/portfolio/diagrams/rubeacon-architecture-dark.svg"
    kpis:
      - label: "잉여 스파이크 조기 거절"
        value: "99.36% (1.17ms)"
        sub: "39,250건 중 38,999건 인메모리 차단"
      - label: "DB 커넥션 풀 보호"
        value: "Pool(10) 고갈 방어"
        sub: "유효 250건만 Redis Streams 적재"
      - label: "게임 서버 메인 틱"
        value: "비동기 스레드 격리"
        sub: "50ms 틱 루프와 네트워크 I/O 완전 분리"
    tasks:
      - id: "task-a"
        topicLabel: "1,000 RPS 스파이크 방어"
        title: "1,000 RPS 스파이크 방어를 위한 2-Tier Redis Lua 및 KEDA 스케일링"
        problem: "마인크래프트 서버는 50ms 주기의 단일 메인 스레드로 동작하여 외부 HTTP 호출이 개입하면 즉시 인게임 랙이 발생합니다. 또한 1,000 RPS 스파이크 유입 시 RDB 비관적 락으로 직접 처리하면 커넥션 풀(HikariCP Pool=10)이 즉시 고갈되어 전체 서비스가 마비되는 위험이 있었습니다."
        solution:
          - "PaperMC 플러그인에서 보상 요청 이벤트를 비동기 워커 풀로 즉시 넘겨 메인 틱(50ms) 블로킹 시간을 0ms로 격리했습니다."
          - "Redis 단일 스레드 환경에서 L1(수량 차감)과 L2(SADD 중복 검사)를 단일 Lua 스크립트로 묶어 유효 250건만 Streams에 적재하고 잉여 38,999건은 1.17ms 안에 즉시 거절했습니다."
          - "K3s의 KEDA가 미처리 메시지 길이를 감지해 Spring Boot 워커 파드를 2-10 Pod로 자동 확장했습니다."
        comparisonHeaders: ["비교 항목", "기존 동기식 RDB 직결 (SELECT FOR UPDATE)", "개선 후 (2-Tier Redis Lua + Streams + KEDA)"]
        comparisonRows:
          - ["1,000 RPS 유입 시 RDB 도달량", "39,250건 전량 DB 커넥션 경합 시도", "유효 250건만 도달 (잉여 38,999건 [99.36%] 인메모리 조기 차단)"]
          - ["평균 거절 응답 지연시간", "커넥션 타임아웃(3,000ms+) 및 연쇄 실패", "평균 1.17ms 내 즉시 거절 (Fast-Fail)"]
          - ["HikariCP(Pool=10) 상태", "즉시 고갈 및 API 응답 불능", "커넥션 고갈 방어, KEDA 워커(2 - 10 Pod)가 정속 소비"]

governanceCases:
  - id: "gov-cloudshield"
    period: "2026.08 - 현재"
    role: "CloudShield 팀장 (협업 파이프라인 구축)"
    title: "계약 기반 병렬 개발 및 역할 분담 영역 격리"
    subtitle: "모의 데이터 체인 및 화이트리스트 CI 하네스를 통한 4인 무충돌 병렬 개발"
    links:
      - label: "PR #112 (계약 복구)"
        url: "https://github.com/mmmphyun/aleph-project/pull/112"
    summary:
      action: "Pydantic v2 계약 모델, 모의 데이터 체인, 디렉터리 화이트리스트 CI 검사기, 교차 계약 테스트"
      result: "이슈 #111(모의 데이터 단절 결함) 식별 후 교차 계약 하네스 구축(PR #112), 이후 모듈 연동 스키마 불일치 재발 0건 및 Git 병합 충돌 0건 달성"
    details:
      problem: "수집 모듈이 미완성된 상태에서 후행 탐지·대응 모듈 개발이 지연되는 병목이 있었습니다. 또한 4인이 각자 도메인을 구현하면서 직무 간 Mock 데이터 체인의 인과관계가 단절되고 룰-매퍼 간 매핑 결함(이슈 #111)이 발생했습니다."
      action: "Pydantic v2 코어 모델에 데이터 규격을 정의하고 모의 데이터 체인을 주입해 병렬 개발을 지원했습니다. 커밋 전 디렉터리 화이트리스트 검사기로 비인가 파일 수정을 차단하고, 수집·탐지·대응 전 구간 교차 계약 테스트 5종을 긴급 구축(PR #112)했습니다."
      result: "선행 결함(이슈 #111) 직후 전 구간 교차 계약 테스트 5종과 화이트리스트 하네스를 구축(PR #112)하여, 이후 최종 배포까지 모듈 연동 스키마 불일치 재발 0건 및 Git 머지 충돌 0건을 유지했습니다."
    stacks:
      - "Pydantic v2"
      - "Git Pre-commit"
      - "GitHub Actions"
      - "pytest"
      - "Notion API"

  - id: "gov-pipeline"
    period: "2026.08 - 현재"
    role: "1인 설계 및 파이프라인 운용"
    title: "기술 문서 배포 파이프라인"
    subtitle: "실습 코드·로그 기반 초안 보조 및 AST/Frontmatter 검증 자동화"
    summary:
      action: "실습 코드·로그 기반 초안 작성 보조, Frontmatter 검증, 엔지니어 최종 검수"
      result: "기술 분석 글 37편 발행: 빌드 타임 정적 검증으로 메타데이터 누락 및 라우팅 깨짐 사전 차단"
    details:
      problem: "강의 자료, 실습 코드, 시스템 로그, 인라인 메모로 정리해둔 내용을 블로그 글로 다시 옮겨 적는 이중 수작업 부담이 있었습니다. 수동 복사 및 발행 과정에서 메타데이터 누락이나 라우팅 링크가 깨지는 문제를 방지해야 했습니다."
      action: "실습 코드와 실행 로그를 바탕으로 표준 구조 초안 작성을 보조했습니다. 자체 Linter 하네스와 Astro/Zod 엔진으로 필수 메타데이터를 빌드 타임에 검사하고, 엔지니어가 직접 재현성과 사실 관계를 최종 검수한 뒤 GitHub Actions로 배포했습니다."
      result: "기술 분석 글 37편을 운영하며 수동 포맷팅 오류를 빌드 단계에서 조기 차단했습니다. 단순 복사 수작업을 줄이고 엔지니어링 기록의 일관성을 확보했습니다."
    stacks:
      - "Python"
      - "Astro"
      - "Zod"
      - "GitHub Actions"
      - "AST Linter"
---

# 포트폴리오 텍스트 단일 신뢰 문서 (Single Source of Truth)

이 문서는 웹 포트폴리오에 주입되는 모든 텍스트(핵심 KPI, 기술 스택 검증 요약, 4대 프로젝트 문제 해결 사례, 비교표, 거버넌스 사례)의 **단일 신뢰 문서(SSOT)**입니다.

- **윤문 및 문체 교정**: 포트폴리오에 쓰이는 모든 서술형 문장은 이 문서의 Frontmatter에서 직접 수정하고 `/humanize-korean` 및 `/detect`를 수행합니다.
- **웹 페이지 동기화**: `portfolio_web_draft.astro`는 이 마크다운 문서의 데이터를 import하여 렌더링하므로, 본 문서만 편집하면 웹 페이지에 자동으로 반영됩니다.
