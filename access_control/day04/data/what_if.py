import os
import sqlite3
import requests

DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")
PEP_URL = os.environ.get("PEP_URL", "http://pep:5000")


def review(con):
    rows = con.execute("""
        SELECT users.name, users.role, assignments.customer
        FROM assignments
        JOIN users
        ON assignments.user_id = users.user_id
        LEFT JOIN permissions
        ON users.role = permissions.role
        AND permissions.action = 'view_assigned_contracts'
        WHERE permissions.action IS NULL
    """).fetchall()
    print("  [규칙 2]", [name + "/" + customer for name, role, customer in rows] or "없음")


def verify():
    cases = [
        ("minsu", "C-1002", 200, {"result", "title", "amount"}),
        ("jiyeon", "C-1003", 200, {"result", "amount"}),
    ]
    for user, contract_id, expected_status, expected_fields in cases:
        reply = requests.get(
            PEP_URL + "/document",
            params={"user": user, "contract": contract_id},
            timeout=3,
        )
        ok = reply.status_code == expected_status and set(reply.json()) == expected_fields
        print("  PASS" if ok else "  FAIL", user, contract_id, reply.status_code, sorted(reply.json()))


con = sqlite3.connect(DB_FILE)
try:
    con.execute("""
        UPDATE users
        SET role = 'account_admin'
        WHERE user_id = 'minsu'
    """)
    con.commit()
    print("김민수가 회계로 옮겼다면:")
    review(con)
    verify()
finally:
    con.execute("""
        UPDATE users
        SET role = 'sales'
        WHERE user_id = 'minsu'
    """)
    con.commit()
    print("되돌린 뒤:")
    review(con)
    verify()
    con.close()