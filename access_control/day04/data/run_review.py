import os
import sqlite3
import requests

DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")
PDP_URL = os.environ.get("PDP_URL", "http://pdp:5001")
APPROVAL_URL = os.environ.get("APPROVAL_URL", "http://approval:5002")
ACTOR_ID = "doyun"

con = sqlite3.connect(DB_FILE)

print("[1] 점검: 담당 고객 권한이 없는 역할의 담당 줄 (규칙 2)")
found = con.execute("""
    SELECT users.user_id, users.name, users.role, assignments.customer
    FROM assignments
    JOIN users
    ON assignments.user_id = users.user_id
    LEFT JOIN permissions
    ON users.role = permissions.role
    AND permissions.action = 'view_assigned_contracts'
    WHERE permissions.action IS NULL
""").fetchall()
if not found:
    print("  없음")

print("[2] 회수: 발견한 담당 줄을 서버로 회수한다")
for user_id, name, role, customer in found:
    reply = requests.post(
        APPROVAL_URL + "/revocations/assignments",
        json={
            "user_id": user_id,
            "customer": customer,
            "actor_id": ACTOR_ID,
            "reason": f"점검 규칙 2: {role} 역할에는 담당 고객 권한이 없음",
        },
        timeout=3,
    )
    print(f"  {name} / {customer}: {reply.status_code} {reply.json()['result']}")

print("[3] 확인: 회수한 직원의 계약 요청을 다시 보낸다")
contracts = con.execute("""
    SELECT contract_id, customer
    FROM contracts
""").fetchall()
for user_id, name, role, customer in found:
    for contract_id, contract_customer in contracts:
        if contract_customer != customer:
            continue
        answer = requests.get(
            PDP_URL + "/check",
            params={"user": user_id, "contract": contract_id},
            timeout=3,
        ).json()
        print(f"  {name} / {contract_id}: {answer['decision']} {answer['reason']}")

print("[4] 검토 목록: 승인 예외와 사용 기록")
for row in con.execute("""
    SELECT access_requests.request_id, users.name,
           access_requests.contract_id, access_requests.reason,
           COUNT(access_log.log_id), MAX(access_log.logged_at)
    FROM access_requests
    JOIN users
    ON access_requests.requester_id = users.user_id
    LEFT JOIN access_log
    ON access_log.user_id = access_requests.requester_id
    AND access_log.contract_id = access_requests.contract_id
    AND access_log.reason = 'APPROVED_REQUEST'
    WHERE access_requests.status = 'APPROVED'
    GROUP BY access_requests.request_id
"""):
    request_id, name, contract_id, reason, count, last = row
    print(f"  {request_id}번 {name} / {contract_id} ({reason}): {count}회, 마지막 {last}")

print("[5] 보고: 회수 이력")
rows = con.execute("""
    SELECT access_changes.changed_at, users.name,
           access_changes.target_kind, access_changes.target_key,
           access_changes.reason
    FROM access_changes
    JOIN users
    ON access_changes.actor_id = users.user_id
""").fetchall()
for changed_at, name, target_kind, target_key, reason in rows:
    print(f"  {changed_at}  {name}  {target_kind} {target_key}  {reason}")
if not rows:
    print("  없음")

con.close()