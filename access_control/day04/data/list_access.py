import os
import sqlite3
import requests

DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")
PDP_URL = os.environ.get("PDP_URL", "http://pdp:5001")


def received(answer):
    parts = []
    if answer["show_title"]:
        parts.append("제목")
    if answer["show_amount"]:
        parts.append("금액")
    return "+".join(parts)


con = sqlite3.connect(DB_FILE)
users = con.execute("""
    SELECT user_id, name
    FROM users
""").fetchall()
contracts = con.execute("""
    SELECT contract_id, customer
    FROM contracts
""").fetchall()
con.close()

for contract_id, customer in contracts:
    print(f"{contract_id} ({customer})")
    for user_id, name in users:
        reply = requests.get(
            PDP_URL + "/check",
            params={"user": user_id, "contract": contract_id},
            timeout=3,
        )
        answer = reply.json()
        if answer["decision"] == "ALLOW":
            print(f"  {name}  ALLOW  {answer['reason']}  {received(answer)}")
        else:
            print(f"  {name}  DENY   {answer['reason']}")