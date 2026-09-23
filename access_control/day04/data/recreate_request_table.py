import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = OFF")

con.execute("""
    CREATE TABLE access_requests_new (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        requester_id TEXT NOT NULL,
        contract_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL CHECK (
            status IN ('PENDING', 'APPROVED', 'REJECTED', 'REVOKED')
        ),
        requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (requester_id) REFERENCES users(user_id),
        FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
    )
""")
con.execute("""
    INSERT INTO access_requests_new
    SELECT *
    FROM access_requests
""")
con.execute("DROP TABLE access_requests")
con.execute("ALTER TABLE access_requests_new RENAME TO access_requests")
con.commit()
con.close()

print("access_requests에 REVOKED 상태를 추가했습니다.")