# 2교시. 누가 확인하고 누가 막는가 — 인증과 판단 서버

import json
import secrets
import ipaddress
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False

with open("company.json", encoding="utf-8") as f:
    company = json.load(f)
USERS = company["users"]
DEVICES = company["devices"]
CONTRACTS = company["contracts"]

PEP_KEY = "PortalKey123"   # 포털과 미리 맞춰 둔 공유키
SESSIONS = {}              # 토큰 -> 로그인한 사용자

def record(event, **fields):
    """판단 한 건을 policy_log.jsonl에 JSON 한 줄로 덧붙인다"""
    # **fields — 이름=값 꼴로 넘어온 인자를 전부 모아 딕셔너리 하나로 받는 표기.
    #   record("login", user="minsu", result="성공") 으로 부르면
    #   event = "login", fields = {"user": "minsu", "result": "성공"} 이 된다.
    #   부르는 곳마다 적을 항목을 마음대로 고를 수 있다.
    entry = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "event": event}
    # entry — 파일에 쓸 한 줄. 시각과 사건 종류를 먼저 넣고,
    entry.update(fields)   # fields의 항목을 뒤에 덧붙인다 -> {"time": ..., "event": "login", "user": "minsu", "result": "성공"}
    with open("policy_log.jsonl", "a", encoding="utf-8") as f:   # "a"는 덧붙이기. 기존 줄은 지우지 않는다
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")    # 딕셔너리를 JSON 한 줄로 바꿔 쓴다

def check_contract(user, device, health, source, cid):
    """계약서 조회 정책 — 어긋나는 첫 조건의 이유를 돌려준다. 전부 통과하면 None"""
    if user not in USERS or not USERS[user]["employed"]:
        return "재직 중인 직원 계정이 아님"
    if CONTRACTS[cid]["customer"] not in USERS[user]["customers"]:
        return "담당 고객의 계약서가 아님"
    if device not in DEVICES or not DEVICES[device]["managed"]:
        return "회사 등록 기기가 아님"
    if DEVICES[device]["owner"] != user:
        return "이 계정에 등록된 기기가 아님"
    if health != "ok":
        return "현재 보안 상태 기준 미충족"
    if not ipaddress.ip_address(source).is_private:
        return "허용되지 않은 접속 경로"
    return None

@app.route("/login", methods=["POST"])
def login():
    if request.headers.get("X-PEP-Key") != PEP_KEY:
        print("[거절] 등록되지 않은 PEP", request.remote_addr)
        return {"result": "거절", "reason": "등록되지 않은 PEP"}, 401
    data = request.get_json()
    user = data.get("user", "")
    password = data.get("password", "")
    if user not in USERS or USERS[user]["password"] != password:
        print("[로그인 실패]", user)
        record("login", user=user, result="실패")
        return {"result": "거절", "reason": "계정 또는 비밀번호가 맞지 않음"}, 401
    token = secrets.token_hex(8)
    SESSIONS[token] = user
    print("[로그인 성공]", user)
    record("login", user=user, result="성공")
    return {"result": "허용", "token": token}

@app.route("/decide", methods=["POST"])
def decide():
    if request.headers.get("X-PEP-Key") != PEP_KEY:
        print("[거절] 등록되지 않은 PEP", request.remote_addr)
        return {"result": "거절", "reason": "등록되지 않은 PEP"}, 401
    data = request.get_json()   # 포털이 모아 보낸 판단 자료
    user = SESSIONS.get(data.get("token", ""))
    cid = data.get("target", "")
    if user is None:
        reason = "로그인 필요"
    elif cid not in CONTRACTS:
        reason = "없는 계약서"
    else:
        reason = check_contract(user, data.get("device", ""), data.get("health", ""), data.get("source", ""), cid)
    result = "허용" if reason is None else "거절"
    print("[판단]", result, user or "(로그인 안 됨)", data.get("device", ""), data.get("source", ""), cid, reason or "")
    record("decide", user=user or "", device=data.get("device", ""), source=data.get("source", ""), target=cid, result=result, reason=reason or "")
    return {"result": result, "reason": reason or "", "user": user or ""}

app.run(port=5002)