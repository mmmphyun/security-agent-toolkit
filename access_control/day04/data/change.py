import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    UPDATE access_requests
    SET status = 'REVOKED'
    WHERE request_id = 1
""")
con.commit()
con.close()

print("한지호의 1번 요청을 REVOKED로 바꿨습니다.")