# 1교시. Zero Trust 이해하기 — 회사망에 들어왔는데 왜 거절될까?

# import json
# import ipaddress
# from flask import Flask, request

# app = Flask(__name__)
# app.json.ensure_ascii = False   # 한글이 \uXXXX로 바뀌지 않게

# with open("company.json", encoding="utf-8") as f:
#     company = json.load(f)
# USERS = company["users"]
# DEVICES = company["devices"]
# CONTRACTS = company["contracts"]

# def check_contract(user, device, health, source, cid):
#     """계약서 조회 정책 — 어긋나는 첫 조건의 이유를 돌려준다. 전부 통과하면 None"""
#     if user not in USERS or not USERS[user]["employed"]:
#         return "재직 중인 직원 계정이 아님"
#     if CONTRACTS[cid]["customer"] not in USERS[user]["customers"]:
#         return "담당 고객의 계약서가 아님"
#     if device not in DEVICES or not DEVICES[device]["managed"]:
#         return "회사 등록 기기가 아님"
#     if DEVICES[device]["owner"] != user:
#         return "이 계정에 등록된 기기가 아님"
#     if health != "ok":
#         return "현재 보안 상태 기준 미충족"
#     if not ipaddress.ip_address(source).is_private:
#         return "허용되지 않은 접속 경로"
#     return None

# @app.route("/contracts/<cid>")
# def read_contract(cid):
#     user = request.headers.get("X-User", "")            # 요청에 실린 사용자 (주장)
#     device = request.headers.get("X-Device", "")        # 요청에 실린 기기 ID (주장)
#     health = request.headers.get("X-Device-Health", "") # 기기 상태 보고
#     source = request.remote_addr                        # 서버가 직접 본 출발지 IP
#     if cid not in CONTRACTS:
#         return {"result": "거절", "reason": "없는 계약서"}, 404
#     reason = check_contract(user, device, health, source, cid)
#     if reason:
#         print("[거절]", user, device, source, cid, reason)
#         return {"result": "거절", "reason": reason}, 403
#     print("[허용]", user, device, source, cid)
#     return CONTRACTS[cid]

# app.run(port=5001)

# 2교시. 누가 확인하고 누가 막는가 — 인증과 판단 서버

import json
import requests
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False

PDP = "http://127.0.0.1:5002"   # 판단 서버
PEP_KEY = "PortalKey123"        # 판단 서버와 미리 맞춰 둔 공유키

with open("company.json", encoding="utf-8") as f:
    company = json.load(f)
CONTRACTS = company["contracts"]   # 포털에는 계약서만 남는다. 계정과 정책은 판단 서버로 갔다.

@app.route("/login", methods=["POST"])
def login():
    # 로그인 요청을 그대로 판단 서버에 넘기고, 받은 답을 그대로 돌려준다
    answer = requests.post(PDP + "/login", json=request.get_json(), headers={"X-PEP-Key": PEP_KEY})
    return answer.json(), answer.status_code

@app.route("/contracts/<cid>")
def read_contract(cid):
    facts = {                                          # 판단에 필요한 자료를 모은다
        "token": request.headers.get("X-Token", ""),
        "device": request.headers.get("X-Device", ""),
        "health": request.headers.get("X-Device-Health", ""),
        "source": request.remote_addr,
        "target": cid,
    }
    answer = requests.post(PDP + "/decide", json=facts, headers={"X-PEP-Key": PEP_KEY}).json()
    if answer["result"] != "허용":                     # 결정대로 집행한다
        print("[거절]", answer.get("user") or "(로그인 안 됨)", cid, answer["reason"])
        return {"result": "거절", "reason": answer["reason"]}, 403
    print("[허용]", answer.get("user", ""), cid)
    return CONTRACTS[cid]

app.run(port=5001)