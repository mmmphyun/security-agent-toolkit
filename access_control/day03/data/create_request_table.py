import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    CREATE TABLE access_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        requester_id TEXT NOT NULL,
        contract_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN ('PENDING', 'APPROVED', 'REJECTED')
        ),
        requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (requester_id) REFERENCES users(user_id),
        FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
    )
""")
con.commit()
con.close()

print("access_requests 표를 만들었습니다.")