import sqlite3

con = sqlite3.connect("/app/db/company.db")

con.execute("""
    CREATE TABLE access_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        user_id TEXT NOT NULL,
        contract_id TEXT NOT NULL,
        decision TEXT NOT NULL,
        reason TEXT NOT NULL
    )
""")
con.commit()
con.close()

print("access_log 표를 만들었습니다.")