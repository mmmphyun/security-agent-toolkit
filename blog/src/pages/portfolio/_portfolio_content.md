---
heroKpis:
  - label: "대응 집계 지연"
    value: "36 - 121ms"
    sub: "DynamoDB 3-AZ 정족수 쿼럼 집계"
  - label: "대륙 간 지연 극복"
    value: "405ms → 16.18ms"
    sub: "96.0% 단축 (RTT 200ms 방어"
  - label: "자동화 검증 게이트"
    value: "291개 테스트"
    sub: "Pydantic V2 계약 및 .tftest.hcl"
  - label: "1,000 RPS 스파이크"
    value: "1.17ms 거절"
    sub: "Redis Lua 99.36% Fast-Fail"

techTiers:
  - tier: "Language & Backend"
    role: "주력 구현 및 트러블슈팅"
    stacks:
      - "Python 3.11+"
      - "FastAPI"
      - "Starlette ASGI"
      - "asyncio"
      - "Pydantic v2"
      - "boto3"
      - "pytest"
      - "Discord.py"
    proof: "순수 ASGI 보안 미들웨어(CSRF, XSS, HSTS 제어), 1GB RAM 스레드 풀 격리 및 단일 게이트 291개 단위 및 계약 테스트 구축"
    links:
      - label: "CloudShield 아키텍처 시리즈"
        url: "/security-agent-toolkit/blog/proj-aleph-project-01-contract-governance-harness/"
      - label: "RPG Sync 엔지니어링 시리즈"
        url: "/security-agent-toolkit/blog/proj-rpg-sync-project-01-problem-definition-and-architecture/"

  - tier: "Infrastructure, Cloud & DB"
    role: "아키텍처 이해 및 실무 연동"
    stacks:
      - "AWS (Lambda, DynamoDB, WAFv2, EC2)"
      - "Terraform (.tftest.hcl)"
      - "Docker"
      - "K3s / KEDA"
      - "PostgreSQL"
      - "Redis (Lua, Streams, Pub/Sub)"
    proof: "DynamoDB 3-AZ 정족수 쿼럼(R+W>N) 슬라이딩 윈도우, PostgreSQL UNIQUE(23505), 배치 업서트 및 Terraform 네이티브 계약 테스트 구축"
    links:
      - label: "DynamoDB 쿼럼 슬라이딩 윈도우"
        url: "/security-agent-toolkit/blog/proj-aleph-project-04-dynamodb-quorum-sliding-window/"
      - label: "ru-beacon 고가용성 아키텍처"
        url: "/security-agent-toolkit/blog/proj-ru-beacon-01-architecture-and-design/"

  - tier: "Research & Spec-Driven"
    role: "보안 표준 및 위협 모델 검증"
    stacks:
      - "Rust (WebAssembly)"
      - "W3C WebAuthn Level 3 (PRF)"
      - "TPM 2.0 (ncrypt.dll FFI)"
      - "AES-256-GCM"
      - "HKDF-SHA256"
    proof: "W3C WebAuthn PRF, TPM 2.0 하드웨어 직접 키 유도 및 Rust Wasm 선형 메모리 zeroize 물리 소거 검증"
    links:
      - label: "PrfVault 연구 분석 포스트"
        url: "/security-agent-toolkit/blog/proj-prfvault-01-wasm-core-and-webauthn-prf/"
      - label: "PrfVault GitHub"
        url: "https://github.com/mmmphyun/PrfVault"

projects:
  - id: "aleph"
    index: "01"
    name: "CloudShield"
    subtitle: "AWS 이벤트 기반 보안 위협 탐지 및 자동 격리 파이프라인"
    domainSummary: "AWS 인프라(VPC, EC2, CloudWatch)에서 발생하는 보안 로그를 실시간 수집하여 무차별 대입 공격 및 침해 시도를 L4/L7 계층에서 자동 격리하고 관제 채널로 전파하는 서버리스 보안 오케스트레이션 파이프라인입니다."
    period: "2026.08 - 2026.11"
    scale: "4인 팀 캡스톤 (팀장)"
    contribution: "기여도 50%"
    repoUrl: "https://github.com/mmmphyun/aleph-project"
    blogLinks:
      - title: "아키텍처 시리즈 (전 4편)"
        url: "/security-agent-toolkit/blog/proj-aleph-project-01-contract-governance-harness/"
    stack:
      - "Python 3.11"
      - "AWS (Lambda, DynamoDB, WAFv2, EC2, CloudWatch)"
      - "Terraform"
      - "Pydantic v2"
      - "pytest (moto)"
    diagramLight: "/security-agent-toolkit/portfolio/diagrams/cloudshield-architecture-light.svg"
    diagramDark: "/security-agent-toolkit/portfolio/diagrams/cloudshield-architecture-dark.svg"
    kpis:
      - label: "슬라이딩 윈도우 지연"
        value: "36 - 121ms"
        sub: "3-AZ 정족수 쿼럼(R+W>N) 조회"
      - label: "5스레드 동시 경합"
        value: "충돌 0건"
        sub: "시간 버킷 1 RTT 원자적 Upsert"
      - label: "자동화 검증 게이트"
        value: "291개 테스트"
        sub: "단위 및 계약 테스트 및 .tftest.hcl"
    tasks:
      - id: "task-a"
        topicLabel: "정족수 쿼럼 & 3-버킷 윈도우"
        title: "분산 복제 쿼럼(R + W > N) 및 시간 버킷 파티셔닝 기반 3-버킷 슬라이딩 윈도우"
        problem: "단일 SSH 공격 세션은 176ms 만에 종료되는 반면 CloudWatch Logs 구독 필터는 로그를 마이크로 배치로 분할 및 순서 역전 전달하여 무상태 Lambda 단독으로는 임계치 탐지가 누락되었습니다. 단일 키 낙관적 락(ConditionExpression) 적용 시 동시 인입 경합으로 갱신 분실이 발생했고 최종 일관성 읽기(R=1) 시 복제 지연 노드를 조회하는 Stale Read 결함이 확인되었습니다."
        solution:
          - "조건식을 제거하고 파티션 키에 시간 버킷 `epoch // 300`을 내장하여 1 RTT 원자적 Upsert를 구현했습니다."
          - "DynamoDB 3-AZ 환경에서 ConsistentRead=True를 적용해 정족수 쿼럼($W=2, R=2$)을 확보하고 최신 LSN 기준으로 직전, 현재, 직후 3개 버킷을 닫힌 구간 $[ref - 300, ref]$으로 스캔하여 샤딩 스트림 순서 역전과 오탐을 함께 해결했습니다."
        comparisonHeaders: ["검증 항목", "단일 키 낙관적 락 / 최종 일관성 읽기", "시간 버킷 락-프리 + 3-버킷 정족수 쿼럼 (채택)"]
        comparisonRows:
          - ["쓰기 동시성 제어", "ConditionExpression 경합 및 CAS 재시도 유실", "epoch // 300 파티셔닝 기반 1 RTT 원자적 Upsert"]
          - ["분산 복제 일관성", "최종 일관성(R=1) 복제 지연 노드로 인한 Stale Read", "정족수 쿼럼(W=2, R=2, R+W>N) 및 Paxos LSN 최신 선별"]
          - ["순서 역전 및 지연", "버킷 경계면 분할 및 지연 배치 탐지 누락", "36 - 121ms 지연 유지 및 단위 테스트 13종 및 8대 시나리오 통과"]

      - id: "task-b"
        topicLabel: "L4 EC2 원자적 격리"
        title: "공유 보안 그룹 폭발 반경 통제 및 아웃바운드 0건 사전 정책 검증"
        problem: "공유 보안 그룹에서 침해 포트 규칙을 개별 회수(revoke)하면 동일 그룹을 쓰는 정상 인스턴스까지 통신이 끊기는 N:M 폭발 반경 위험이 있었습니다. 또한 AWS 보안 그룹 생성 시 기본 주입되는 아웃바운드 전체 허용(0.0.0.0/0) 규칙이나 사후 주입된 포트 규칙이 잔존할 경우 C2 서버 유출을 막지 못하는 함정이 존재했습니다."
        solution:
          - "인스턴스 단위로 보안 그룹 배열을 단일 트랜잭션 치환하는 modify_instance_attribute(Groups=[target_sg_id])를 채택해 타 정상 워크로드 트래픽 간섭을 배제했습니다."
          - "교체 실행 전 validate_quarantine_security_group을 통해 인바운드와 아웃바운드 규칙이 모두 빈 배열([])인지 사전 검증하고 이미 바인딩된 그룹이라도 규칙 오염 감지 시 즉시 실패(False)를 반환해 사후 오염을 방어했습니다."
        comparisonHeaders: ["비교 항목", "공유 보안 그룹 규칙 개별 삭제", "사전 정책 검증 + 격리 SG 원자적 교체 (채택)"]
        comparisonRows:
          - ["타 인스턴스 영향", "공유 SG 소속 정상 워크로드 연쇄 통신 단절", "침해 인스턴스 eth0만 핀포인트 고립 (폭발 반경 제어)"]
          - ["아웃바운드 통제", "AWS 기본 아웃바운드 허용 규칙 잔존 위험", "인바운드 및 아웃바운드 규칙 0건 사전 검증 통과 시에만 교체"]
          - ["중복 호출 및 오염 방어", "반복 API 호출 및 사후 규칙 오염 미인지", "상태 기반 멱등 처리 및 규칙 오염 시 즉시 거부"]

      - id: "task-c"
        topicLabel: "L7 WAFv2 LockToken 제어"
        title: "외부 분산 락을 배제한 AWS WAFv2 네이티브 LockToken 낙관적 동시성 제어"
        problem: "다수의 Lambda 인스턴스가 동시에 WAFv2 IPSet을 갱신할 때 선행 커밋된 차단 IP가 덮어써지는 갱신 분실 위험이 있었고 광범위한 서브넷(/24, /16) 인입 시 정상 사용자 대규모 오차단 위험이 존재했습니다. 이를 막기 위해 외부 Redis 락을 도입하면 VPC 연결 지연으로 10초 관통 예산을 위협했습니다."
        solution:
          - "외부 락 인프라를 배제하고 IPv4 유효성 검사 및 /32 단일 호스트 프리픽스 강제 검증으로 서브넷 오차단을 진입단에서 거부했습니다."
          - "get_ip_set 조회 직후 인메모리에서 기차단 여부를 확인해 불필요한 LockToken 소모를 막고 WAFOptimisticLockException 충돌 시 최신 토큰을 재조회해 최대 3회 재시도하는 루프로 Moto 단위 및 통합 테스트 10종을 전건 통과했습니다."
        comparisonHeaders: ["검증 항목", "단순 덮어쓰기 / 외부 분산 락 도입", "WAFv2 네이티브 LockToken + 상태 멱등성 (채택)"]
        comparisonRows:
          - ["동시 갱신 정합성", "후행 커밋의 덮어쓰기 유실 또는 외부 락 네트워크 지연", "네이티브 LockToken 검증 및 최대 3회 재시도로 전건 보존"]
          - ["오차단 폭발 반경", "비정상 대역(/16, /24) 인입 시 정상 트래픽 대량 차단", "/32 단일 호스트 강제 검증 및 비정상 서브넷 즉시 거부"]
          - ["토큰 경합 억제", "중복 경보마다 쓰기 호출로 연쇄 토큰 충돌 유발", "인메모리 선제 멱등 판정으로 불필요한 쓰기 API 생략"]

      - id: "task-d"
        topicLabel: "Pydantic V2 계약 & Terraform .tftest.hcl"
        title: "Pydantic V2 불변 계약 하네스(이슈 #111 방어) 및 Terraform 6개 모듈 .tftest.hcl 통합 게이트"
        problem: "4인 병렬 개발 중 Mock 데이터 스키마 불일치로 모듈 간 이벤트 체인이 단절(이슈 #111)되었고 인프라 코드에서는 제로패딩 CIDR 별칭 입력 시 보안 그룹 검증을 우회할 위험이 있었습니다."
        solution:
          - "이슈 #111을 방어하기 위해 Pydantic V2 불변 데이터 모델(frozen=True)과 7대 액션 교차 계약 테스트 test_contracts.py, 비인가 경로 수정을 차단하는 verify_rnr_scope.py를 선제 구축했습니다."
          - "인프라 영역은 6개 모듈(vpc, ec2, dynamodb, waf, lambda, quarantine_sg)로 격리 분리하고 mock_provider 기반 .tftest.hcl을 도입해 제로패딩 CIDR 별칭 거부와 격리 SG 인, 아웃 0건 불변식을 플랜 단계에서 자동 검증했습니다."
          - "위 두 계층의 하드가드를 GitHub Actions CI에 결합하여 291개 테스트 게이트를 통과해야만 머지되도록 파이프라인을 확립했습니다."
        comparisonHeaders: ["비교 항목", "수동 코드 리뷰 및 배포 후 검증", "Terraform .tftest.hcl + CI 계약 하드가드 (채택)"]
        comparisonRows:
          - ["IaC 보안 규칙 검증", "실제 AWS 배포 후에야 규칙 누락 및 별칭 우회 확인", "mock_provider 기반 .tftest.hcl로 플랜 단계 즉시 차단"]
          - ["직무 간 스키마 정합성", "모듈 통합 시점 런타임 역직렬화 오류 발생", "Pydantic V2 불변 계약 및 291개 테스트 통과 시에만 머지"]
          - ["작업 영역 침범 방어", "타 직무 파일 임의 수정으로 병합 충돌 발생", "verify_rnr_scope.py로 비인가 경로 수정 시 CI 즉시 거부"]

  - id: "rpg-sync"
    index: "02"
    name: "RPG Sync System"
    subtitle: "이기종 플랫폼 간 상태 동기화 및 인게임 가이드 백엔드"
    domainSummary: "마인크래프트 서버와 Discord 봇, FastAPI 웹 위키 포털로 파편화된 유저 신원, 역할, 직업 데이터를 단일 진실 공급원 기준으로 실시간 동기화하는 백엔드 시스템입니다."
    period: "2026.04 - 2026.07"
    scale: "개인 프로젝트 (1인 단독 개발 및 실운영)"
    contribution: "기여도 100%"
    repoUrl: "https://github.com/mmmphyun/rpg_sync_project"
    blogLinks:
      - title: "엔지니어링 시리즈 (전 6편)"
        url: "/security-agent-toolkit/blog/proj-rpg-sync-project-01-problem-definition-and-architecture/"
    stack:
      - "Python 3.11"
      - "FastAPI (Starlette ASGI)"
      - "Discord.py"
      - "asyncio"
      - "PostgreSQL (Supabase)"
      - "Redis"
      - "Docker"
      - "Cloudflare (R2, CDN)"
    diagramLight: "/security-agent-toolkit/portfolio/diagrams/rpg-sync-architecture-light.svg"
    diagramDark: "/security-agent-toolkit/portfolio/diagrams/rpg-sync-architecture-dark.svg"
    kpis:
      - label: "평균 응답 지연"
        value: "405ms → 16.18ms"
        sub: "96.0% 단축, Fast Path 캐시 결합"
      - label: "메인 루프 지터"
        value: "206ms → 14.64ms"
        sub: "92.9% 억제, 동기 I/O 풀 격리"
      - label: "소켓 단절 및 타임아웃"
        value: "6/6 복구 및 오류 0건"
        sub: "@db_retry 및 3초 defer 방어"
    tasks:
      - id: "task-a"
        topicLabel: "분산 온보딩 & 3초 타임아웃 격리"
        title: "비동기 분산 온보딩 파이프라인: 디스코드 3초 타임아웃 방어 및 일회용 매직링크 인증"
        problem: "북미 Mojang API 조회와 원격 DB 쓰기 트랜잭션이 직렬 결합되어 디스코드의 3초 인터랙션 타임아웃(Interaction failed)을 초과했습니다. 또한 수작업 계정 확인 및 권한 부여로 인해 운영진 온보딩 시간이 건당 30분 이상 소요되는 운영 정체와 계정 중복 도용 위험이 상존했습니다."
        solution:
          - "모달 제출 즉시 선제 defer 응답(15분 유예 토큰)을 발급하고 aiohttp.TCPConnector 전역 세션 풀 재활용으로 3초 타임아웃 오류를 0건으로 통제했으며, Redis INCR 기반 3회 연속 오입력 잠금(1시간 TTL)으로 외부 API 429 차단을 방어했습니다."
          - "진입 경계에서 RFC 4122 표준 36자리 UUID로 정규화하고 PostgreSQL UNIQUE 제약(23505 예외 매핑)으로 계정 도용을 차단했습니다."
          - "5분 만료 일회용 매직링크를 웹 DB 트랜잭션 내 조회 즉시 폐기하고 Redis Pub/Sub 기반 인게임 역할 자동 부여와 연동하여 운영자 개입 시간을 건당 30분 이상에서 5분 이내로 단축했습니다."
        comparisonHeaders: ["검증 항목", "단발성 동기 호출 / 수기 온보딩 (개선 전)", "선제 defer + 경계 정규화 + 일회용 매직링크 (개선 후)"]
        comparisonRows:
          - ["3초 게이트웨이 타임아웃", "원격 DB 쓰기 지연 결합 시 Interaction failed 빈발", "선제 defer 토큰 및 전역 세션 풀링으로 타임아웃 오류 0건"]
          - ["계정 도용 및 오입력 방어", "중복 바인딩 방치 및 무제한 재시도로 429 위험", "PostgreSQL UNIQUE(23505) 매핑 및 Redis 3회 오입력 즉시 잠금"]
          - ["인증 보안 및 온보딩 시간", "수기 안내 건당 30분 이상 소요", "트랜잭션 내 토큰 즉시 폐기, JWT 쿠키 연동으로 5분 이내 단축"]

      - id: "task-b"
        topicLabel: "순수 ASGI 보안 미들웨어"
        title: "Starlette 순수 ASGI 보안 미들웨어(SecurityMiddleware) 및 다계층 XSS 및 CSRF 방어"
        problem: "비동기 Fetch API로 JSON 데이터를 받아 브라우저 DOM에 렌더링할 때 템플릿 자동 이스케이프가 작동하지 않는 클라이언트 XSS 사각지대가 존재했습니다. 또한 단순 문자열 접두사 비교 기반 출처 검증은 유사 도메인 CSRF 우회에 취약했고 HSTS 헤더 일괄 주입 시 로컬 개발 환경에서 브라우저 접근이 차단되는 문제가 발생했습니다."
        solution:
          - "일반 텍스트는 escapeHTML(5대 특수문자 치환)로 격리하고 마크다운 서식 영역은 marked.parse 직후 DOMPurify.sanitize를 체이닝해 악성 스크립트와 인라인 이벤트 핸들러(onerror 등)를 제거했습니다."
          - "외부 라이브러리 없이 순수 ASGI 표준 SecurityMiddleware를 구현해 상태 변경 요청(POST, PUT, PATCH, DELETE)의 Origin/Referer가 허용 도메인과 완전 일치하거나 슬래시(/) 경계로 끝나는지 검증하여 비정상 요청을 라우터 진입 전 403 Forbidden으로 차단했습니다."
          - "응답 인터셉터(send_wrapper)에서 X-Frame-Options: DENY, CSP(frame-ancestors 'none'), nosniff를 주입하고 호스트가 localhost/127.0.0.1일 때는 HSTS 주입을 제외해 개발 환경 락아웃을 방지했습니다."
        comparisonHeaders: ["보안 위협 영역", "프레임워크 기본 설정 의존 (개선 전)", "다계층 XSS 소독 + 순수 ASGI 미들웨어 (개선 후)"]
        comparisonRows:
          - ["동적 DOM 렌더링 XSS", "Fetch JSON 렌더링 시 스크립트 페이로드 실행 위험", "escapeHTML + DOMPurify 체이닝으로 악성 태그 무해화 검증"]
          - ["상태 변경 요청 CSRF", "단순 접두사 비교로 유사 도메인(.attacker.com) 우회 가능", "도메인 경계 일치 검증으로 비정상 출처 403 즉시 차단"]
          - ["보안 헤더 및 로컬 호환성", "클릭재킹 노출 또는 로컬호스트 HSTS 영구 락아웃", " 필수 보안 헤더 전역 주입 및 호스트 감지 기반 HSTS 조건부 분기"]

      - id: "task-c"
        topicLabel: "계층형 파서 & 배치 업서트"
        title: "비정형 마크다운 계층형 컨텍스트 버퍼 파서 및 사전 캐싱 기반 배치 업서트"
        problem: "80여 개 직업 설명문에 '과거 영웅이었으나 빌런이 되었다' 같은 서사가 포함될 때 단순 키워드 포함 검사 방식은 진영을 오분류했고 거대 정규표현식 단일 파싱은 줄바꿈 불일치 시 역추적(Backtracking) 병목을 유발했습니다. 또한 축약 닉네임(가문명 생략) 관습으로 인해 단순 부분 일치 적용 시 동명이인 오매핑 위험이 높았습니다."
        solution:
          - "메타데이터 브래킷과 조건문 캡슐화 태그 문법을 정의하고 문서를 라인 단위로 순회하며 헤더 계층 전환 시 버퍼를 배출하는 선형 시간 복잡도 파서 _flush_job을 구현했습니다."
          - "80여 개 직업 목록을 인메모리에 사전 캐싱한 뒤 1차 완전 일치 -> 2차 부분 일치 순으로 검증하고 후보가 2개 이상 검출되면 임의 매핑을 보류하고 실패 리포트로 격리했습니다."
          - "사전 검증을 통과한 유효 유저 집합만 PostgreSQL ON CONFLICT DO UPDATE 구문과 executemany 벌크 업서트로 연동해 트랜잭션 전체 롤백 위험을 제거했습니다."
        comparisonHeaders: ["처리 단계", "단순 키워드 검색 / 개별 쿼리 실행", "계층형 버퍼 파서 + 사전 캐싱 배치 업서트 (채택)"]
        comparisonRows:
          - ["서사 텍스트 파싱", "본문 내 동일 단어 간섭으로 진영 오분류 및 정규식 병목", "브래킷 및 태그 캡슐화 및 라인 순회 버퍼 플러시로 정확도 확보"]
          - ["축약 닉네임 직업 매칭", "단순 부분 일치 시 동일 가문명 캐릭터 오매핑 발생", "인메모리 사전 캐싱 + 2단계 매칭 및 중복 후보 예외 격리"]
          - ["데이터베이스 적재", "유저별 개별 쿼리 호출 및 예외 시 전체 롤백 위험", "검증 통과군 대상 ON CONFLICT DO UPDATE 일괄 executemany"]

      - id: "task-d"
        topicLabel: "200ms DB 커넥션 자가 치유"
        title: "대륙 간 200ms DB 커넥션 자가 치유 및 Fail-Open 캐시 서킷 브레이커"
        problem: "미국 오리건(GCP)과 서울(DB) 간 200ms 물리 RTT 환경에서 매 질의마다 실행되던 SELECT 1 사전 검증 쿼리로 인해 단순 API 응답이 405.66ms까지 지연되었고 관리형 DB의 유휴 세션 강제 종료 시 봇 프로세스가 중단되었습니다. 또한 1GB RAM 단일 노드에서 캐시 메모리 폭증과 캐시 장애 전파를 막아야 했습니다."
        solution:
          - "사전 검증 쿼리를 제거하고 OS 커널 TCP 파라미터(keepidle=30, keepintvl=10, keepcnt=5)로 유휴 소켓을 관리했습니다."
          - "Docker Compose에서 Redis 메모리를 50MB(volatile-lru)로 제한해 메타데이터를 사전 예열하고 Redis 장애 시 프로세스 중단 없이 DB 직접 조회로 즉시 폴백하는 Fail-Open 서킷 브레이커와 @db_retry 소켓 자가 치유 데코레이터를 구축했습니다."
        comparisonHeaders: ["단계", "개선 조치", "평균 응답 지연 (초당 처리량)"]
        comparisonRows:
          - ["개선 전", "매 요청마다 SELECT 1 사전 검증", "405.66ms (2.47 RPS)"]
          - ["1단계 개선", "사전 검증 제거 + OS TCP Keepalive", "243.41ms (4.11 RPS)"]
          - ["2단계 개선", "Redis 50MB 예열 + Fail-Open 서킷 브레이커", "16.18ms (61.78 RPS, 25배 증대)"]
          - ["3단계 자가 치유", "@db_retry 자동 커넥션 폐기 및 재생성", "소켓 강제 종료 6회 주입 시 6/6건 전건 복구 (4.77ms)"]

      - id: "task-e"
        topicLabel: "1GB RAM 워커 풀 & 분산 락"
        title: "1GB RAM 비동기 루프 벌크헤드 격리, Safe TTL 분산 락 및 오프라인 상태 대사"
        problem: "단일 스레드 asyncio 루프 안에서 동기식 DB 질의(psycopg2)가 메인 루프를 200ms 이상 점유하여 웹소켓 하트비트 전송이 지연되고 게이트웨이 세션이 끊어졌습니다. 또한 다중 운영진 동시 승인 시 중복 처리 경합과 봇 재부팅 중 발생한 상태 불일치를 해결해야 했습니다."
        solution:
          - "전용 스레드 풀(ThreadPoolExecutor, 최대 20개)과 DB 커넥션 풀 상한(최대 8개)으로 벌크헤드 격리를 적용해 메인 이벤트 루프의 하트비트 지터를 92.9% 억제했습니다."
          - "1GB RAM 제약에 맞춰 무거운 Redlock 데몬 대신 Redis SET NX EX 15 Safe TTL 단발성 락과 DB 원자적 조건부 갱신(WHERE is_guide_completed = false)을 결합하고 재기동 시 PostgreSQL 원천 진실 기반 단일 대사 쿼리로 누락 상태를 복구했습니다."
        comparisonHeaders: ["성능 및 신뢰성 지표", "단일 이벤트 루프 (개선 전)", "벌크헤드 격리 + Safe TTL + 상태 대사 (개선 후)"]
        comparisonRows:
          - ["웹소켓 하트비트 지터", "206.04ms (세션 단절 빈발)", "14.64ms (92.9% 지터 억제)"]
          - ["10건 병렬 요청 처리 시간", "2.495초 (순차 블로킹)", "0.358초 (85.7% 처리 시간 단축)"]
          - ["20건 동시 승인 및 오프라인 복구", "중복 승인 발생 및 재기동 시 상태 유실", "1건 선점, 19건 차단 검증 및 오프라인 20건 23.58ms 복구"]

  - id: "prfvault"
    index: "03"
    name: "PrfVault"
    subtitle: "하드웨어 보안 키 기반 무상태 자격증명 아키텍처"
    domainSummary: "중앙 서버 침해와 마스터 비밀번호 탈취 위협을 제거하기 위해 W3C WebAuthn Level 3 prf 확장과 하드웨어 보안 칩(TPM 2.0)을 연동하여 브라우저 Wasm 격리 메모리 내에서 대칭키를 즉석 유도 및 소거하는 무상태 자격증명 보관소 연구입니다."
    period: "2026.09 - 2026.10"
    scale: "개인 연구 (1인)"
    contribution: "기여도 100%"
    repoUrl: "https://github.com/mmmphyun/PrfVault"
    blogLinks:
      - title: "연구 분석 포스트"
        url: "/security-agent-toolkit/blog/proj-prfvault-01-wasm-core-and-webauthn-prf/"
    stack:
      - "Rust (WebAssembly)"
      - "TypeScript (Chrome MV3)"
      - "W3C WebAuthn Level 3 (PRF)"
      - "TPM 2.0 (ncrypt.dll FFI)"
      - "AES-256-GCM / HKDF-SHA256"
      - "Playwright"
    diagramLight: "/security-agent-toolkit/portfolio/diagrams/prfvault-architecture-light.svg"
    diagramDark: "/security-agent-toolkit/portfolio/diagrams/prfvault-architecture-dark.svg"
    kpis:
      - label: "마스터 키 디스크 저장"
        value: "0건 (제로화)"
        sub: "TPM 2.0 엔클레이브 직접 유도"
      - label: "메모리 노출 국소화"
        value: "수 ms 단위 소거"
        sub: "Rust Wasm zeroize 물리 덮어쓰기"
      - label: "통합 테스트 및 실태 계측"
        value: "17/17건 통과"
        sub: "국내 50대 웹사이트 인증 실태 계측"
    tasks:
      - id: "task-a"
        topicLabel: "TPM 2.0 하이브리드 폴백"
        title: "Windows OS의 WebAuthn PRF 차단 규명 및 Native Host(ncrypt.dll FFI) 폴백 구현"
        problem: "인텔 PTT TPM 2.0 실기 환경에서 Windows 11 운영체제 계층(webauthn.dll)이 내장 플랫폼 인증자에 대해 W3C WebAuthn PRF 확장 평가를 거부하는 플랫폼 한계를 확인했습니다."
        solution:
          - "표준 WebAuthn 진입점을 유지하되 PRF 확장 거부를 감지하면 즉시 Chrome Native Messaging Host로 전환되는 하이브리드 폴백 파이프라인을 구축했습니다."
          - "네이티브 호스트에서 Windows CNG API(ncrypt.dll)를 Rust C-FFI로 직접 바인딩하여 TPM 2.0 하드웨어 엔클레이브 내부에서 256비트 대칭키를 유도하고 디스크 영구 저장을 배제했습니다."
        comparisonHeaders: ["검증 영역", "플랫폼 한계 및 위협", "엔지니어링 구현 및 검증 결과"]
        comparisonRows:
          - ["플랫폼 PRF 확장 차단", "Windows webauthn.dll의 내장 TPM PRF 호출 거부", "Native Messaging Host 및 ncrypt.dll C-FFI 자동 폴백 구현"]
          - ["마스터 키 영구 저장 위협", "디스크 볼트 파일 탈취 시 오프라인 무차별 대입 위험", "TPM 2.0 하드웨어 직접 유도로 디스크 상 키 저장 0건"]
          - ["파이프라인 무결성 검증", "크로스 레이어 키 유도 및 AES-256-GCM 암호화 및 복호화", "crypto_core 3건 + native_host 14건 총 17개 케이스 전건 통과"]

      - id: "task-b"
        topicLabel: "Wasm zeroize & 50대 사이트 계측"
        title: "Rust Wasm 선형 메모리 물리 소거(zeroize) 및 국내 50대 웹사이트 인증 실태 계측"
        problem: "브라우저 JavaScript 런타임은 가비지 컬렉터(GC)의 메모리 해제 시점을 개발자가 강제할 수 없어 복호화된 평문 패스워드가 브라우저 힙 덤프에 장시간 노출되는 한계가 있었습니다."
        solution:
          - "암호화 및 복호화 코어를 Rust WebAssembly로 구현해 JS 힙과 분리된 Wasm 선형 메모리 내부로 평문 연산을 격리하고 연산 직후 zeroize 트레이트로 바이트 배열을 즉시 0으로 덮어써 노출 창을 수 밀리초 이내로 국소화했습니다."
          - "Playwright 자동화 스크립트로 국내 트래픽 상위 50대 웹사이트의 인증 폼을 전수 계측하여 16자 비밀번호 길이 제한 정책으로 인한 섀넌 정보 엔트로피 20.0% 손실 및 가상 키패드의 자동 완성 차단율(6.7%)을 정량 도출했습니다."
        comparisonHeaders: ["검증 영역", "기존 브라우저 런타임 및 웹 환경", "엔지니어링 구현 및 계측 결과"]
        comparisonRows:
          - ["메모리 평문 잔류", "JS GC 비결정적 수거로 힙 덤프 시 평문 노출", "Rust Wasm 선형 메모리 격리 및 연산 직후 zeroize 물리 소거"]
          - ["패스워드 엔트로피 실태", "레거시 웹사이트의 비밀번호 최대 길이 제한(16자)", "국내 50대 사이트 전수 계측으로 섀넌 엔트로피 20.0% 손실 규명"]
          - ["클라이언트 주입 호환성", "비표준 마우스 입력 가상 키패드 강제 사이트", "6.7% 가상 키패드 차단율 계측 및 표준 입력 전환 근거 도출"]

  - id: "ru-beacon"
    index: "04"
    name: "ru-beacon"
    subtitle: "1,000 RPS 스파이크 방어를 위한 2-Tier Redis Lua 및 KEDA 비동기 파이프라인"
    domainSummary: "대규모 인게임 선착순 보상 이벤트 시 발생하는 1,000 RPS 순간 스파이크 트래픽으로부터 게임 서버 메인 틱(50ms)과 RDB 커넥션 풀을 보호하기 위해 설계한 비동기 이벤트 파이프라인 및 K3s 오토스케일링 인프라입니다."
    period: "2026.06 - 2026.07"
    scale: "개인 아키텍처 연구 (1인)"
    contribution: "기여도 100%"
    repoUrl: "https://github.com/mmmphyun/ru-beacon"
    blogLinks:
      - title: "고가용성 아키텍처 분석 포스트"
        url: "/security-agent-toolkit/blog/proj-ru-beacon-01-architecture-and-design/"
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
        value: "Pool(10) 고갈 0건"
        sub: "유효 250건만 Redis Streams 적재"
      - label: "게임 서버 메인 틱"
        value: "0ms 블로킹"
        sub: "50ms 틱 루프와 네트워크 I/O 완전 분리"
    tasks:
      - id: "task-a"
        topicLabel: "1,000 RPS Lua Fast-Fail"
        title: "1,000 RPS 스파이크 방어를 위한 2-Tier Redis Lua 원자적 Fast-Fail 게이트키퍼"
        problem: "선착순 보상 이벤트로 1,000 RPS 스파이크 트래픽(총 39,250건)이 유입될 때 RDB 비관적 락으로 직접 처리하면 HikariCP 커넥션 풀이 즉각 고갈되어 전체 API가 타임아웃으로 마비되는 한계가 있었습니다."
        solution:
          - "Redis 단일 스레드 원자성을 활용해 L1(잔여 재고 차감)과 L2(SADD 기반 유저 중복 수령 검증)를 단일 Lua 스크립트로 묶어 컨텍스트 스위칭과 레이스 컨디션을 배제했습니다."
          - "선착순을 통과한 유효 요청 250건만 `Redis Streams` 큐에 적재하고 잉여 요청 38,999건(99.36%)은 RDB에 도달하기 전 인메모리에서 평균 1.17ms 만에 즉시 거절했습니다."
        comparisonHeaders: ["비교 항목", "기존 동기식 RDB 직결 (SELECT FOR UPDATE)", "개선 후 (2-Tier Redis Lua + Redis Streams)"]
        comparisonRows:
          - ["1,000 RPS 유입 시 RDB 도달량", "39,250건 전량 DB 커넥션 경합 시도", "유효 250건만 도달 (잉여 38,999건 [99.36%] 인메모리 조기 차단)"]
          - ["평균 거절 응답 지연시간", "커넥션 타임아웃(3,000ms+) 및 연쇄 실패", "평균 1.17ms 내 즉시 거절 (Fast-Fail)"]
          - ["HikariCP(Pool=10) 상태", "즉시 고갈 및 API 응답 불능", "커넥션 고갈 0건 달성 및 유효 트래픽만 비동기 큐잉"]

      - id: "task-b"
        topicLabel: "메인 틱 격리 & KEDA 스케일링"
        title: "PaperMC 메인 틱(50ms) 비동기 스레드 격리 및 K3s KEDA 큐 길이 기반 오토스케일링"
        problem: "마인크래프트(PaperMC) 서버는 50ms(20 TPS) 주기의 단일 메인 스레드에서 월드 연산을 수행하므로 외부 HTTP 호출이 개입하면 즉시 인게임 틱 지연이 발생했습니다. 또한 비동기 I/O 워커 특성상 대기 큐가 밀려도 CPU 사용률이 낮아 기존 Kubernetes CPU HPA가 스케일아웃을 트리거하지 못하는 맹점이 확인되었습니다."
        solution:
          - "PaperMC 플러그인에서 보상 요청 이벤트를 비동기 워커 스레드 풀로 즉시 위임하고 지수 백오프 재시도를 결합해 게임 메인 틱(50ms) 블로킹 시간을 0ms로 격리했습니다."
          - "K3s 클러스터에 KEDA를 연동하고 Redis Streams 미처리 메시지 적체량(Pending/Lag)을 직접 감시하는 트리거를 구성해 워커 파드를 최소 2개에서 최대 10개까지 탄력 확장했으며 RDB 복합 유니크 제약과 XACK 확인 응답으로 최소 1회 처리 및 멱등성을 보장했습니다."
        comparisonHeaders: ["검증 항목", "메인 스레드 동기 호출 / CPU 기반 HPA", "비동기 워커 격리 + KEDA Streams 트리거 (채택)"]
        comparisonRows:
          - ["게임 서버 메인 틱(50ms)", "외부 HTTP 응답 대기 중 월드 연산 멈춤 발생", "비동기 스레드 풀 즉시 위임으로 메인 틱 블로킹 0ms"]
          - ["오토스케일링 트리거 반응", "I/O 대기 중 낮은 CPU율로 인해 스케일아웃 미작동", "Redis Streams 큐 적체 감지 즉시 워커 2 → 10 Pod 확장"]
          - ["장애 복구 및 영속 멱등성", "워커 재시작 시 메시지 유실 또는 중복 지급 위험", "Consumer Group PEL(XPENDING) 재처리 및 RDB 복합 유니크 방어"]

governanceCases:
  - id: "gov-cloudshield"
    period: "2026.08 - 현재"
    role: "CloudShield 팀장 (협업 파이프라인 구축)"
    title: "계약 기반 병렬 개발 및 역할 분담 영역 격리"
    subtitle: "모의 데이터 체인 및 화이트리스트 CI 하네스를 통한 4인 무충돌 병렬 개발"
    links:
      - label: "PR #112 (계약 복구)"
        url: "https://github.com/mmmphyun/aleph-project/pull/112"
      - label: "거버넌스 아키텍처 포스트"
        url: "/security-agent-toolkit/blog/proj-aleph-project-01-contract-governance-harness/"
    summary:
      action: "Pydantic v2 불변 계약 모델, 모의 데이터 체인, 디렉터리 화이트리스트 CI 검사기, 291개 자동화 테스트"
      result: "이슈 #111(모의 데이터 단절 결함) 식별 후 교차 계약 하네스 구축(PR #112), 이후 모듈 연동 스키마 불일치 재발 0건 및 Git 병합 충돌 0건 유지"
    details:
      problem: "수집 모듈이 미완성된 상태에서 후행 탐지 및 대응 모듈 개발이 지연되는 병목이 있었습니다. 또한 4인이 각자 도메인을 구현하면서 직무 간 Mock 데이터 체인의 인과관계가 단절되고 룰-매퍼 간 매핑 결함(이슈 #111)이 발생했습니다."
      action: "Pydantic v2 코어 모델에 불변 데이터 규격을 정의하고 모의 데이터 체인을 주입해 병렬 개발을 지원했습니다. 디렉터리 화이트리스트 검사기로 비인가 파일 수정을 차단하고 수집, 탐지, 대응 전 구간 교차 계약 테스트를 구축(PR #112)했습니다."
      result: "선행 결함(이슈 #111) 직후 교차 계약 테스트와 화이트리스트 하네스를 구축(PR #112)하여 단일 게이트 291개 테스트 체계를 확립하고 이후 모듈 연동 스키마 불일치 재발 0건 및 비인가 파일 수정 즉시 차단을 검증했습니다."
    stacks:
      - "Pydantic v2"
      - "Git Pre-commit"
      - "GitHub Actions"
      - "pytest"
      - "Terraform Test"

  - id: "gov-pipeline"
    period: "2026.08 - 현재"
    role: "1인 설계 및 파이프라인 운용"
    title: "기술 문서 검증 및 배포 파이프라인"
    subtitle: "실제 코드 경로 대조 검증기 및 AST/Frontmatter 린터 자동화"
    links:
      - label: "파이프라인 설계 시리즈"
        url: "/security-agent-toolkit/blog/proj-devlog-agent-pipeline-01-architecture-and-tradeoffs/"
    summary:
      action: "로컬 코드 경로 실재성 검증기, 마크다운 AST/Frontmatter 린터, GitHub Actions 정적 배포"
      result: "심층 프로젝트 분석 포스트 14편을 포함한 기술 문서 배포 시 허위 코드 참조 및 문법 오류를 빌드 단계에서 사전 차단"
    details:
      problem: "실습 코드, 시스템 로그, 트러블슈팅 메모를 기술 블로그 포스트로 정리할 때 존재하지 않는 파일 경로가 인용되거나 다이어그램 및 수식 문법, 메타데이터가 깨지는 결함을 방지해야 했습니다."
      action: "로컬 저장소의 실제 파일 및 심볼 실재성을 대조하는 파이썬 하네스 검증기와 Astro/Zod 스키마 린터를 빌드 파이프라인에 배치하고 검증을 통과한 문서만 GitHub Pages로 배포했습니다."
      result: "심층 프로젝트 분석 14편을 포함한 기술 분석 문서를 운영하며 허위 코드 참조와 포맷팅 오류를 빌드 타임에 조기 차단하고 엔지니어링 기록의 사실성을 확보했습니다."
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
