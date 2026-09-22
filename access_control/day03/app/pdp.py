import os
import sqlite3
from datetime import datetime, timezone, timedelta
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False
DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")


def ask(question, values=()):
    with sqlite3.connect(DB_FILE) as connection:
        return connection.execute(question, values).fetchall()


LOG_FILE = os.environ.get("LOG_FILE")
KST = timezone(timedelta(hours=9))


def log(line):
    text = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S") + " " + line
    print(text, flush=True)
    if LOG_FILE:
        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(text + "\n")


def approved_request_exists(user, contract_id):
    rows = ask("""
        SELECT 1
        FROM access_requests
        JOIN access_decisions
        ON access_requests.request_id = access_decisions.request_id
        WHERE access_requests.requester_id = ?
        AND access_requests.contract_id = ?
        AND access_requests.status = 'APPROVED'
        AND access_decisions.decision = 'APPROVED'
    """, (user, contract_id))

    return bool(rows)


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

    if approved_request_exists(user, contract_id):
        return "ALLOW", "APPROVED_REQUEST"

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
        return "ALLOW", "ROLE_PERMISSION"

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
    return "ALLOW", "ASSIGNED_CUSTOMER"


@app.get("/check")
def check():
    user = request.args.get("user", "")
    contract_id = request.args.get("contract", "")
    decision, reason = decide(user, contract_id)

    show_title = False
    show_amount = False
    if decision == "ALLOW" and reason == "APPROVED_REQUEST":
        show_title = True
        show_amount = True
    elif decision == "ALLOW":
        rows = ask("""
            SELECT permissions.action
            FROM users
            JOIN permissions
            ON users.role = permissions.role
            WHERE users.user_id = ?
        """, (user,))
        actions = [row[0] for row in rows]
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
    }, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)