import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    DELETE FROM access_decisions
    WHERE request_id = 2
""")
con.execute("""
    UPDATE access_requests
    SET status = 'PENDING'
    WHERE request_id = 2
""")

con.commit()
con.close()

print("2번 요청을 다시 PENDING으로 준비했습니다.")