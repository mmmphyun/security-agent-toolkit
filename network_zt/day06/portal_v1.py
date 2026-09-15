# 1교시. Zero Trust 이해하기 — 회사망에 들어왔는데 왜 거절될까?

import json
import ipaddress
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False   # 한글이 \uXXXX로 바뀌지 않게

with open("company.json", encoding="utf-8") as f:
    company = json.load(f)
CONTRACTS = company["contracts"]

@app.route("/contracts/<cid>")
def read_contract(cid):
    source = request.remote_addr                      # 요청을 보낸 PC의 IP
    inside = ipaddress.ip_address(source).is_private  # 사내 대역(사설 주소)인가
    if not inside:
        print("[거절]", source, cid, "회사 밖에서 온 요청")
        return {"result": "거절", "reason": "회사 밖에서 온 요청"}, 403
    if cid not in CONTRACTS:
        return {"result": "거절", "reason": "없는 계약서"}, 404
    print("[허용]", source, cid)
    return CONTRACTS[cid]

app.run(port=5001)