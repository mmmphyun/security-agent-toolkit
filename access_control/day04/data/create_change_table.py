import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    CREATE TABLE access_changes (
        change_id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_kind TEXT NOT NULL,
        target_key TEXT NOT NULL,
        action TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (actor_id) REFERENCES users(user_id)
    )
""")
con.execute("""
    INSERT INTO permissions
    VALUES ('auditor', 'revoke_access')
""")
con.commit()
con.close()

print("이력 표와 회수 권한을 준비했습니다.")