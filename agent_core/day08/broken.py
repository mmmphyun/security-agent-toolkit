# 5교시. 디버깅 — 고장난 파이프라인 고치기

# 고장난 코드 — 오타도 에러도 없지만 세 곳이 틀리게 돈다
RANK = {"high": 0, "medium": 1, "low": 2}

def sort_key(r):
    return RANK[r["severity"]]

judgments = [
    {"rule": "night_login", "severity": "medium", "summary": "새벽 로그인 관찰 등록"},
    {"rule": "brute_force", "severity": "high", "summary": "관리자 계정 잠금 실행"},
    {"rule": "port_scan", "severity": "high", "summary": "포트 스캔 IP 차단 실행"},
]

high_count = 0
for j in judgments:
    if j["severity"] == "high":
        high_count += 1 # 기존 코드: high_count = 1

if high_count == 0: # 기존 코드: if high_count > 0:
    warning = "특이 사항 없음"
else:
    warning = f"**주의: high 경보 {high_count}건**"

lines = ""
for j in sorted(judgments, key=sort_key):
    lines += f"- [{j['severity']}] {j['rule']}: {j['summary']}\n" # 기존 코드: lines = f"- [{j['severity']}] {j['rule']}: {j['summary']}\n"


report = f"""# 야간 요약

- high 경보: {high_count}건
- {warning}

## 건별 내역
{lines}"""
print(report)


'''
Q. 컴파일 에러도, 런타임 에러도 없는 조용한 에러의 경우 디버깅툴 또는 의심 지점 콘솔 출력 등을 사용해 디버깅을 하는데, 실무의 대규모 레거시 시스템에서는 디버깅을 어떻게 진행해?
A. 실무의 대규모 레거시 시스템에서는 질문하신 print 출력문 삽입이나 로컬 GUI 디버거(Breakpoint) 방식의 사용이 매우 제한적.
    상태 오염 및 재현 불가, 배포 제약, 볼륨 문제 때문.
    
    따라서 실무에서는 '코드를 직접 멈추거나 수정하는 방식' 대신 관측 가능성(Observability) 도구와 격리 기법을 조합하여 조용한 논리 에러(Silent Logical Failure)를 추적함.

    1. 구조화된 로그와 상관관계 ID(Correlation ID) 추적
    단순 문자열 출력이 아닌, 요청마다 고유한 추적 ID(예: trace_id, request_id)를 부여한 JSON 형태의 구조화된 로그(Structured Logging)를 사용합니다.
    Kibana, Datadog, CloudWatch 등 로그 수집기에서 문제의 트랜잭션 ID 하나만 필터링하여, 여러 마이크로서비스나 모듈을 거치는 데이터의 중간 입출력 상태와 분기 경로를 시간 순서대로 역추적합니다.
    로그 레벨이 평소에는 INFO이더라도, 특정 사용자/요청 세션에 대해서만 동적으로 DEBUG 로그를 활성화(Dynamic Log Level)하여 런타임 데이터를 확인합니다.

    2. 입력/출력 덤프 기반의 로컬 리플레이(Replay) 환경 구축
    운영 환경에서 '조용한 에러'를 유발한 실제 입력 데이터(페이로드, DB 스냅샷)를 추출합니다.
    이 데이터를 로컬 또는 격리된 스테이징 환경의 단위/통합 테스트 케이스로 그대로 주입(Regression Test 작성)하여 버그 상황을 100% 재현(Reproduce)시킵니다.
    버그가 로컬 테스트에서 완전히 재현된 시점부터는 안전하게 로컬 디버거(pdb, IDE 디버거)를 붙여 단계별 메모리 상태를 추적합니다.

    3. 무중단 런타임 프로파일링 및 APM/Tracing
    코드를 수정하지 않고 OpenTelemetry, Sentry, Datadog 등의 APM(Application Performance Monitoring) 에이전트를 통해 함수별 호출 횟수, 실행 시간, 인자값의 메타데이터를 추적합니다.
    데이터가 비정상적으로 필터링되거나(예: 100건 조회 후 0건 반환), 조용히 None 또는 빈 배열이 반환되는 병목/이상 구간을 Span 단위로 좁힙니다.

    4. 이진 탐색 기법 (Git Bisect 및 데이터 파이프라인 단절)
    레거시 코드 특성상 "언제부터 이 로직이 잘못 동작했는가"를 파악하기 위해 git bisect를 사용해 정상 동작했던 커밋과 현재 커밋 사이를 이진 탐색하여 로직 결함이 유입된 커밋을 격리합니다.
    데이터 파이프라인이라면 입력단과 출력단 사이의 중간 저장소(Redis, DB, 큐)의 데이터 정합성을 검증하여, 에러가 발생한 컴포넌트 경계를 절반씩 좁혀나갑니다.

(요약하면 이해가 안돼서 그대로 붙여넣음.)
'''