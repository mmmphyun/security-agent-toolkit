import os
import sqlite3

DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")

con = sqlite3.connect(DB_FILE)
con.execute("PRAGMA foreign_keys = ON")
try:
    con.execute("BEGIN")
    con.execute("""
        DELETE FROM assignments
        WHERE user_id = 'minsu'
        AND customer = 'C상사'
    """)
    raise RuntimeError("이력 저장 직전에 오류가 났다고 가정")
    con.execute("""
        INSERT INTO access_changes (
            target_kind, target_key, action, actor_id, reason
        )
        VALUES ('assignment', 'minsu/C상사', 'REVOKE', 'doyun', '실험')
    """)
    con.commit()
except Exception as error:
    con.rollback()
    print("되돌렸습니다:", error)
finally:
    con.close()