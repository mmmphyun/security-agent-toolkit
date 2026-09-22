import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    CREATE TABLE access_decisions (
        request_id INTEGER PRIMARY KEY,
        approver_id TEXT NOT NULL,
        decision TEXT NOT NULL CHECK (
            decision IN ('APPROVED', 'REJECTED')
        ),
        note TEXT NOT NULL,
        decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES access_requests(request_id),
        FOREIGN KEY (approver_id) REFERENCES users(user_id)
    )
""")

con.execute("""
    INSERT INTO permissions
    VALUES ('auditor', 'approve_access_requests')
""")

con.commit()
con.close()

print("결정 표와 승인 권한을 준비했습니다.")