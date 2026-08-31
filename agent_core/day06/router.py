# 5교시. 도구 호출 라우터 — 머리와 손 사이의 검문소

def lock_account(alert):
    print(f"[조치] 계정 잠금: {alert['user']}")
    return "locked"

def block_ip(alert):
    print(f"[조치] IP 차단: {alert['ip']}")
    return "blocked"

def watch(alert):
    print(f"[조치] 관찰 대상 등록: {alert['rule']}")
    return "watching"

tools = {"lock_account": lock_account, "block_ip": block_ip, "watch": watch}

judgments = [
    {
        "rule": "brute_force",
        "severity": "high",
        "summary": "admin 계정에 5회 연속 로그인 실패 — 무차별 대입 의심",
        "tool": "lock_account",
        "alert": {"rule": "brute_force", "user": "admin"},
    },
    {
        "rule": "password_spraying",
        "severity": "high",
        "summary": "해외 IP 한 곳이 여러 계정에 로그인 시도 — 패스워드 스프레잉 의심",
        "tool": "block_ip",
        "alert": {"rule": "password_spraying", "ip": "185.220.101.34"},
    },
    {
        "rule": "night_login",
        "severity": "medium",
        "summary": "새벽 3시 admin 해외 로그인 — 지켜볼 필요",
        "tool": "watch",
        "alert": {"rule": "night_login"},
    },
]

results = []
for judgment in judgments:
    name = judgment["tool"]
    print(f"[접수] {judgment['rule']} — 심각도 {judgment['severity']}, 권장 조치 {name}")
    '''
    예시 코드 구조 보고 생긴 의문
    Q. 작업 실행 후 출력이 되어야 이전 작업이 잘 마무리되었음을 알 수 있지 않아? 
    A. 실무 로깅 및 작업 처리 파이프라인 관점에서 "실행 전 로그"와 "실행 완료 로그"는 명확히 분리되어야 함.
        실제 작업 도중 예외가 발생해 실패하더라도 콘솔에는 이미 성공적으로 조치된 것처럼 상태 왜곡 우려.
        작업의 '시작'과 '성공/실패'가 구분되지 않아 시스템 모니터링 시 트랜잭션의 실제 완료 여부 확신 불가.
        ∴ 접수 및 시작 로그 -> 작업 실행 -> 결과 및 완료 로그
    '''
    if name not in tools:                                # 검문 1 — 과제 1 그대로
        print(f"[거부] {name} — 허용 목록에 없는 도구")
        judgment["result"] = "rejected"
        judgment['reason'] = "허용 목록에 없는 도구"
        results.append(judgment)
        continue

    if judgment["severity"] == "high":
        print(f"[검토] {judgment['summary']}")
        approve = input(f"{judgment['tool']} 조치를 실행할까요? (y/n): ")

        if approve == "n":
            judgment['result'] = "held"
            judgment['reason'] = "담당자 미승인"
            results.append(judgment)
            print(f"[보류] {judgment['rule']} — 담당자가 승인하지 않음")
            continue

    result = tools[name](judgment["alert"])
    judgment['result'] = "approved"
    results.append(judgment)

print(f"[완료] {len(results)}건 처리")