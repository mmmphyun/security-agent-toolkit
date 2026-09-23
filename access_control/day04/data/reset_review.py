import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    DELETE FROM assignments
    WHERE user_id = 'sora'
    AND customer = 'B전자'
""")
con.execute("""
    INSERT INTO assignments (user_id, customer)
    VALUES ('sora', 'B전자')
""")
con.execute("""
    UPDATE access_requests
    SET status = 'APPROVED'
    WHERE request_id = 1
""")
con.execute("DELETE FROM access_changes")
con.commit()
con.close()

print("회수 전 상태로 되돌렸습니다.")