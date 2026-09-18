# PEP(집행 서버): 요청을 받으면 PDP에 묻고, 허용일 때만 계약서를 준다.
import os
import sqlite3
from datetime import datetime, timezone, timedelta
import requests
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False

# 회사 데이터베이스의 위치.
DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")


def ask(question, values=()):
    # 요청이 올 때마다 데이터베이스에 물어본다.
    with sqlite3.connect(DB_FILE) as connection:
        return connection.execute(question, values).fetchall()


# PDP의 주소. compose.yaml에서 서비스 이름으로 넘겨준다.
PDP_URL = os.environ.get("PDP_URL", "http://pdp:5001")

# 기록 파일의 위치. 따로 정하지 않으면 화면(docker logs)에만 남긴다.
LOG_FILE = os.environ.get("LOG_FILE")
KST = timezone(timedelta(hours=9))  # 한국 시간


def log(line):
    # 한 줄을 시각과 함께 화면에 찍고, LOG_FILE이 정해져 있으면 파일 끝에도 덧붙인다.
    text = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S") + " " + line
    print(text, flush=True)
    if LOG_FILE:
        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(text + "\n")


@app.get("/document")  # 사용자가 묻는다: /document?user=minsu&contract=C-1001
def document():
    user = request.args.get("user", "")
    contract_id = request.args.get("contract", "")

    try:
        reply = requests.get(PDP_URL + "/check", params={"user": user, "contract": contract_id}, timeout=3)
        answer = reply.json()
    except requests.RequestException as error:
        # PDP에 닿지 못했다. 판단을 모르면 계약서를 주지 않는다(fail-closed).
        log(f"[PEP] user={user} contract={contract_id} PDP_ERROR {type(error).__name__}")
        return {"result": "DENY", "reason": "PDP_ERROR"}, 503

    log(f"[PEP] user={user} contract={contract_id} {answer['decision']} {answer['reason']}")
    if answer["decision"] != "ALLOW":
        return {"result": "DENY", "reason": answer["reason"]}, 403

    rows = ask("SELECT title, amount FROM contracts WHERE contract_id = ?", (contract_id,))
    title, amount = rows[0]
    return {"result": "ALLOW", "title": title, "amount": amount}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)