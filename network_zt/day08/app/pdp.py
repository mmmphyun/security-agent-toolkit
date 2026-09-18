# PDP(판단 서버): 회사 파일을 읽고, 누가 어떤 계약서를 봐도 되는지 판단만 한다.
import json
import os
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False

# 회사 파일의 위치. 따로 정하지 않으면 이미지 안에 복사된 company.json을 읽는다.
COMPANY_FILE = os.environ.get("COMPANY_FILE", "company.json")

with open(COMPANY_FILE, encoding="utf-8-sig") as file:
    company = json.load(file)


def decide(user, contract_id):
    # Day 6의 판단 순서와 같다. 거절 이유를 글자로 돌려준다.
    if user not in company["users"]:
        return "DENY", "UNKNOWN_USER"
    if company["users"][user]["employed"] != True:
        return "DENY", "NOT_EMPLOYED"
    if contract_id not in company["contracts"]:
        return "DENY", "UNKNOWN_CONTRACT"
    customer = company["contracts"][contract_id]["customer"]
    if customer not in company["users"][user]["customers"]:
        return "DENY", "NOT_ASSIGNED"
    return "ALLOW", "OK"


@app.get("/check")  # PEP가 묻는다: /check?user=minsu&contract=C-1001
def check():
    user = request.args.get("user", "")
    contract_id = request.args.get("contract", "")
    decision, reason = decide(user, contract_id)
    print(f"[PDP] user={user} contract={contract_id} {decision} {reason}", flush=True)
    return {"decision": decision, "reason": reason}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
