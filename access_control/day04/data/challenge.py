# 4교시 찾은 권한을 회수하고 이력을 남기자
import sqlite3

keyword = input("검색어: ")

con = sqlite3.connect("/app/db/company.db")
rows = con.execute("""
    SELECT access_changes.changed_at, users.name,
           access_changes.target_kind, access_changes.target_key,
           access_changes.reason
    FROM access_changes
    JOIN users
    ON access_changes.actor_id = users.user_id
    WHERE access_changes.reason LIKE ?
""", ("%" + keyword + "%",)).fetchall()
con.close()

for changed_at, name, target_kind, target_key, reason in rows:
    print(f"{changed_at}  {name}  {target_kind} {target_key}  {reason}")



# 3교시 접근 기록을 표에 넣어 쓰지 않는 권한을 찾자
# import sqlite3

# contract_id = input("계약 번호: ")

# con = sqlite3.connect("/app/db/company.db")
# rows = con.execute("""
#     SELECT access_log.logged_at, users.name, access_log.decision
#     FROM access_log
#     JOIN users
#     ON access_log.user_id = users.user_id
#     WHERE access_log.contract_id = ?
#     ORDER BY access_log.logged_at DESC
# """, (contract_id,)).fetchall()
# con.close()

# for logged_at, name, decision in rows:
#     print(f"{logged_at}  {name}  {decision}")



# 2교시 필요 없어진 권한을 규칙으로 찾자

# import sqlite3

# employee_name = input("직원 이름: ")

# con = sqlite3.connect("/app/db/company.db")
# rows1 = con.execute("""
#     SELECT assignments.customer
#     FROM assignments
#     JOIN users
#     ON assignments.user_id = users.user_id
#     WHERE users.employed = 0
#     AND users.name = ?
# """, (employee_name,)).fetchall()
# rows2 = con.execute("""
#     SELECT users.role, assignments.customer
#     FROM assignments
#     JOIN users
#     ON assignments.user_id = users.user_id
#     LEFT JOIN permissions
#     ON users.role = permissions.role
#     AND permissions.action = 'view_assigned_contracts'
#     WHERE permissions.action IS NULL
#     AND users.name = ?
# """, (employee_name,)).fetchall()
# con.close()

# for (customer,) in rows1:
#     print(f"{employee_name}: 퇴사했지만 {customer} 담당 줄이 남아 있다.")
# for role, customer in rows2:
#     print(f"{employee_name}: {role} 역할인데 {customer} 담당 줄이 남아 있다.")
# if not rows1 and not rows2:
#     print("점검 항목 없음")



# 1교시 지금 누가 무엇을 볼 수 있는지 확인하자

# import os
# import sqlite3
# import requests

# DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")
# PDP_URL = os.environ.get("PDP_URL", "http://pdp:5001")

# contract_id = input("계약 번호: ")

# con = sqlite3.connect(DB_FILE)
# users = con.execute("""
#     SELECT user_id, name
#     FROM users
# """).fetchall()
# con.close()

# for user_id, name in users:
#     reply = requests.get(
#         PDP_URL + "/check",
#         params={"user": user_id, "contract": contract_id},
#         timeout=3,
#     )
#     answer = reply.json()
#     if answer["decision"] == "ALLOW":
#         print(f"{name} ({answer['reason']})")