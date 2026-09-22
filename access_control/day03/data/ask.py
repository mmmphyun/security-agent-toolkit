import sqlite3

con = sqlite3.connect("/app/db/company.db")

row = con.execute("""
    SELECT access_requests.status,
           access_decisions.decision,
           access_decisions.approver_id
    FROM access_requests
    JOIN access_decisions
    ON access_requests.request_id = access_decisions.request_id
    WHERE access_requests.request_id = 2
""").fetchone()

print(row)
con.close()