import sqlite3

con = sqlite3.connect("/app/db/company.db")

print("[규칙 1] 퇴사한 직원에게 담당 줄이나 승인 예외가 남아 있다")
rows = con.execute("""
    SELECT users.name, assignments.customer
    FROM assignments
    JOIN users
    ON assignments.user_id = users.user_id
    WHERE users.employed = 0
""").fetchall()
for name, customer in rows:
    print(f"  {name}: 담당 {customer}")
rows2 = con.execute("""
    SELECT users.name, access_requests.contract_id
    FROM access_requests
    JOIN users
    ON access_requests.requester_id = users.user_id
    WHERE users.employed = 0
    AND access_requests.status = 'APPROVED'
""").fetchall()
for name, contract_id in rows2:
    print(f"  {name}: 승인 예외 {contract_id}")
if not rows and not rows2:
    print("  없음")

print("[규칙 2] 담당 고객 권한이 없는 역할의 직원에게 담당 줄이 있다")
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
for name, role, customer in rows:
    print(f"  {name} ({role}): 담당 {customer}")
if not rows:
    print("  없음")

con.close()