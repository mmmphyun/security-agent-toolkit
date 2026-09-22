import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("DELETE FROM access_decisions")
con.execute("DELETE FROM access_requests")
con.execute("""
    DELETE FROM sqlite_sequence
    WHERE name = 'access_requests'
""")

con.commit()
con.close()

print("요청과 결정 기록을 비웠습니다.")