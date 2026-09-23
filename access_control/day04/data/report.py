import sqlite3

con = sqlite3.connect("/app/db/company.db")

for row in con.execute("""
    SELECT access_requests.request_id,
           requester.name,
           access_requests.contract_id,
           access_requests.status,
           approver.name,
           access_decisions.note
    FROM access_requests
    LEFT JOIN access_decisions
    ON access_requests.request_id = access_decisions.request_id
    JOIN users AS requester
    ON access_requests.requester_id = requester.user_id
    LEFT JOIN users AS approver
    ON access_decisions.approver_id = approver.user_id
"""):
    print(row)

con.close()
