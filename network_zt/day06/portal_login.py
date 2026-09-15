# 2교시. 누가 확인하고 누가 막는가 — 인증과 판단 서버

import json
import secrets
import ipaddress
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False

with open("company.json", encoding="utf-8") as f:
    company = json.load(f)
USERS = company["users"]
DEVICES = company["devices"]
CONTRACTS = company["contracts"]

SESSIONS = {}   # 토큰 -> 로그인한 사용자

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
    data = request.get_json()                    # {"user": ..., "password": ...}
    user = data.get("user", "")
    password = data.get("password", "")
    if user not in USERS or USERS[user]["password"] != password:
        print("[로그인 실패]", user, request.remote_addr)
        return {"result": "거절", "reason": "계정 또는 비밀번호가 맞지 않음"}, 401
    token = secrets.token_hex(8)                 # 16자리 무작위 토큰
    SESSIONS[token] = user
    print("[로그인 성공]", user, "토큰", token)
    return {"result": "허용", "token": token}

@app.route("/contracts/<cid>")
def read_contract(cid):
    token = request.headers.get("X-Token", "")
    user = SESSIONS.get(token)                   # 토큰이 없거나 모르는 토큰이면 None
    device = request.headers.get("X-Device", "")
    health = request.headers.get("X-Device-Health", "")
    source = request.remote_addr
    if user is None:
        print("[거절]", "(로그인 안 됨)", device, source, cid, "로그인 필요")
        return {"result": "거절", "reason": "로그인 필요"}, 401
    if cid not in CONTRACTS:
        return {"result": "거절", "reason": "없는 계약서"}, 404
    reason = check_contract(user, device, health, source, cid)
    if reason:
        print("[거절]", user, device, source, cid, reason)
        return {"result": "거절", "reason": reason}, 403
    print("[허용]", user, device, source, cid)
    return CONTRACTS[cid]

app.run(port=5001)