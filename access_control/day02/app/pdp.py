# PDP(판단 서버): 회사 데이터베이스를 읽고, 누가 어떤 계약서를 봐도 되는지 판단만 한다.
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False

# 회사 데이터베이스의 위치.
DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")


def ask(question, values=()):
    # 요청이 올 때마다 데이터베이스에 물어본다. 표를 고치면 다음 요청부터 바로 반영된다.
    with sqlite3.connect(DB_FILE) as connection:
        return connection.execute(question, values).fetchall()


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


def decide(user, contract_id):
    rows = ask("""
        SELECT employed
        FROM users
        WHERE user_id = ?
    """, (user,))
    if not rows:
        return "DENY", "UNKNOWN_USER"
    if rows[0][0] != 1:
        return "DENY", "NOT_EMPLOYED"

    rows = ask("""
        SELECT customer
        FROM contracts
        WHERE contract_id = ?
    """, (contract_id,))
    if not rows:
        return "DENY", "UNKNOWN_CONTRACT"
    customer = rows[0][0]

    rows = ask("""
        SELECT permissions.action
        FROM users
        JOIN permissions
        ON users.role = permissions.role
        WHERE users.user_id = ?
        AND permissions.action IN (
            'view_all_amounts',
            'view_all_contract_titles'
        )
    """, (user,))
    if rows:
        return "ALLOW", "OK"

    rows = ask("""
        SELECT 1
        FROM users
        JOIN permissions
        ON users.role = permissions.role
        WHERE users.user_id = ?
        AND permissions.action = 'view_assigned_contracts'
    """, (user,))
    if not rows:
        return "DENY", "NO_VIEW_PERMISSION"

    rows = ask("""
        SELECT 1
        FROM assignments
        WHERE user_id = ?
        AND customer = ?
    """, (user, customer))
    if not rows:
        return "DENY", "NOT_ASSIGNED"
    return "ALLOW", "OK"


@app.get("/check")
def check():
    user = request.args.get("user", "")
    contract_id = request.args.get("contract", "")
    decision, reason = decide(user, contract_id)

    show_title = False
    show_amount = False
    if decision == "ALLOW":
        rows = ask("""
            SELECT permissions.action
            FROM users
            JOIN permissions
            ON users.role = permissions.role
            WHERE users.user_id = ?
        """, (user,))

        actions = []
        for row in rows:
            actions.append(row[0])

        if "view_assigned_contracts" in actions:
            show_title = True
            show_amount = True
        if "view_all_contract_titles" in actions:
            show_title = True
        if "view_all_amounts" in actions:
            show_amount = True

    log(f"[PDP] user={user} contract={contract_id} {decision} {reason}")
    return {
        "decision": decision,
        "reason": reason,
        "show_title": show_title,
        "show_amount": show_amount,
    }, 200, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
