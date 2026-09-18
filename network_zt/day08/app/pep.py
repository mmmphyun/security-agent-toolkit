# PEP(집행 서버): 요청을 받으면 PDP에 묻고, 허용일 때만 계약서를 준다.
import json
import os
import requests
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False

# 회사 파일의 위치. 따로 정하지 않으면 이미지 안에 복사된 company.json을 읽는다.
COMPANY_FILE = os.environ.get("COMPANY_FILE", "company.json")

with open(COMPANY_FILE, encoding="utf-8-sig") as file:
    company = json.load(file)

# PDP의 주소. compose.yaml에서 서비스 이름으로 넘겨준다.
PDP_URL = os.environ.get("PDP_URL", "http://pdp:5001")


@app.get("/document")  # 사용자가 묻는다: /document?user=minsu&contract=C-1001
def document():
    user = request.args.get("user", "")
    contract_id = request.args.get("contract", "")

    try:
        reply = requests.get(PDP_URL + "/check", params={"user": user, "contract": contract_id}, timeout=3)
        answer = reply.json()
    except requests.RequestException as error:
        # PDP에 닿지 못했다. 판단을 모르면 계약서를 주지 않는다(fail-closed).
        print(f"[PEP] user={user} contract={contract_id} PDP_ERROR {type(error).__name__}", flush=True)
        return {"result": "DENY", "reason": "PDP_ERROR"}, 503

    print(f"[PEP] user={user} contract={contract_id} {answer['decision']} {answer['reason']}", flush=True)
    if answer["decision"] != "ALLOW":
        return {"result": "DENY", "reason": answer["reason"]}, 403

    contract = company["contracts"][contract_id]
    return {"result": "ALLOW", "title": contract["title"], "amount": contract["amount"]}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
