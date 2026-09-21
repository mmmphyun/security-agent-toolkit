import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    INSERT INTO roles
    VALUES ('auditor')
""")
con.execute("""
    INSERT INTO users
    VALUES ('doyun', '김도윤', 'auditor', 1)
""")
con.commit()
con.close()