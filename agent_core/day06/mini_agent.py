# 4교시. AI Agent와 Tool-use — 판단에 손을 달아주다

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()                    # .env 파일을 읽어 온다 (Day 4)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"   # LLM 서비스의 창구 주소
headers = {"Authorization": "Bearer " + os.getenv("GEMINI_API_KEY"), "Content-Type": "application/json"}   # 통행증(키)을 싣는 자리

CHOICE_FORMAT = {
    "type": "json_schema",              # 설계도 방식으로 강제한다
    "json_schema": {
        "name": "choice",                   # 설계도 이름 (아무거나)
        "schema": {
            "type": "object",               # 답은 딕셔너리 모양
            "properties": {                 # 가질 키들
                "tool": {"type": "string", "enum": ["lock_account", "block_ip", "watch", "alert_team"]},   # 이 세 이름 밖은 나올 수 없다
                "reason": {"type": "string"},                                                # 고른 이유 한 문장
            },
            "required": ["tool", "reason"],         # 둘 다 필수
        },
    },
}

def parse_judgment(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("[파싱 실패] JSON이 아니다:", text[:40])
        return None

def lock_account(alert):
    print(f"[조치] 계정 잠금: {alert['user']}")
    return "locked"

def block_ip(alert):
    print(f"[조치] IP 차단: {alert['ip']}")
    return "blocked"

def watch(alert):
    print(f"[조치] 관찰 대상 등록: {alert['rule']}")
    return "watching"

def alert_team(alert):
    print(f"[조치] 담당팀 호출: {alert['rule']}")

tools = {"lock_account": lock_account, "block_ip": block_ip, "watch": watch, "alert_team": alert_team}

alert = {"rule": "unknown_malware", "user": "svc-backup", "ip": "10.0.0.7", "detail": "백신이 분류하지 못한 실행 파일이 서버 여러 대에서 동시에 실행됨"}

prompt = "다음 보안 경보에 적절한 도구를 골라라.\n경보: " + json.dumps(alert, ensure_ascii=False) + """

쓸 수 있는 도구 목록:
- lock_account: 계정이 공격받고 있을 때 그 계정을 잠근다
- block_ip: 특정 IP가 공격을 보낼 때 그 IP를 차단한다
- watch: 확실하지 않을 때 관찰 대상으로만 등록한다
- alert_team: 즉시 사람의 판단이 필요할 때 담당팀을 부른다"""

body = {
    "model": "gemini-3.5-flash-lite",
    "messages": [
        {"role": "system", "content": "너는 보안 관제 어시스턴트다."},
        {"role": "user", "content": prompt},
    ],
    "response_format": CHOICE_FORMAT,   # 설계도를 요청에 싣는다
}

response = requests.post(url, headers=headers, json=body)   # 요청을 보내고 응답을 받는다
answer = response.json()["choices"][0]["message"]["content"]   # 응답에서 답 문장만 꺼낸다

choice = parse_judgment(answer)   # 글자를 딕셔너리로 — 실패하면 None

if choice:
    name = choice["tool"]
    result = tools[name](alert)
    print(f"[완료] {name} → {result}")




'''
오늘 강의 - 캡스톤 프로젝트 연계 질문
Q. 보안 측면에서 바라보았을 때 ai 에이전트의 판단으로 툴을 실행시키는 것 자체도 굉장히 위험해보이는데, 실무에서는 어떻게 이를 방어해?
A. 'Zero Trust' 원칙을 기본으로 설계함. 간접 프롬프트 인젝션, 데이터 유출, 시스템 파괴 명령 실행 등의 위험을 방어하기 위해 계층화된 다중 방어 체계를 적용.
    (최소 권한 원칙, 결정적 인자 검증, HITL (Human-in-the-Loop) 승인 메커니즘, 툴 출력 필터링)

Q. 그렇다면 에이전트 프레임워크는 보안 사고를 빠르게 감지하고 사람에게 알려주는 보수적인 방향으로만 쓰이고 있어?
A. 사고 파급도(Impact)와 가역성(Reversibility)에 따른 통제된 자동화 방식으로 운영

Q. 해당 룰은 사람이 정의하는데, 휴먼 에러는? 또, 에이전트의 위험도 과소평가로 인한 오동작이 일어난다면?
A. 에이전트는 저위험 함수는 호출할 수 있지만 고위험 API는 에이전트의 툴셋에 절대 넣지 않음. + 툴 호출 시 강제로 승인 대기 큐로 밀어넣음.
    룰 기반 자동화(SOAR Playbook, WAF 정책, IaC)의 휴먼 에러 검증 파이프라인 존재.(Dry-Run, Blast Radius(영향 반경) 제한 및 Rate Limiting, Policy as Code (PaC) 및 CI/CD 검증)

Q. 자동화를 위한 툴셋이 해커에게 사용하기 좋은 도구가 되는 경우는?
A. (1)간접 프롬프트 인젝션을 통한 에이전트 툴 하이재킹, (2)과도한 권한을 가진 Service Account 탈취, (3)자동화 워크플로우를 역이용한 서비스 거부, (4)툴 인자 주입을 통한 원격 코드 실행

Q. 위 4가지 경우는 코드단에서 방어하는지?
A. (1)외부 데이터를 읽는 에이전트와 쓰기/전송 툴을 가진 에이전트의 물리적 분리(Dual LLM Pattern), 네트워크 아웃바운드 차단 [인프라/아키텍처 대응]
    (2)최소 권한(Least Privilege) 원칙 적용, 장기 인증서(Long-lived Token) 대신 임시 STS/OIDC 토큰 발급, 단일 작업 단위의 세부 권한 분리 [인프라/IAM 대응]
    (3)차단 대상 검증 시 하드코딩된 불변 화이트리스트로 등록하여 툴 실행 전 강제 무시 처리, 단위 시간당 차단 횟수 제한 [코드단 대응]
    (4)문자열 기반 커맨드 조립 금지(shell=True, 문자열 포맷팅 금지), Pydantic/Enum 기반의 엄격한 타입 및 화이트리스트 파라미터 유효성 검증, ORM/파라미터화된 쿼리 사용 [코드단 대응]
        툴 실행 환경 자체를 격리된 일회성 컨테이너(gVisor, Firecracker microVM) 내에서 구동 [인프라 대응]
'''