import sqlite3

con = sqlite3.connect("/app/db/company.db")

# 표 셋을 만든다.
con.execute("""CREATE TABLE users (
    user_id   TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    role      TEXT NOT NULL,
    employed  INTEGER NOT NULL
)""")
con.execute("""CREATE TABLE assignments (
    user_id   TEXT NOT NULL,
    customer  TEXT NOT NULL
)""")
con.execute("""CREATE TABLE contracts (
    contract_id TEXT PRIMARY KEY,
    customer    TEXT NOT NULL,
    title       TEXT NOT NULL,
    amount      TEXT NOT NULL
)""")

# 자료를 넣는다.
con.execute("INSERT INTO users VALUES ('minsu',  '김민수', 'sales',         1)")
con.execute("INSERT INTO users VALUES ('jiyeon', '박지연', 'account_admin', 1)")
con.execute("INSERT INTO users VALUES ('hana',   '이하나', 'sales',         0)")
con.execute("INSERT INTO users VALUES ('sora',   '정소라', 'sales',         1)")
con.execute("INSERT INTO users VALUES ('yuna',   '최유나', 'sales',         1)")
con.execute("INSERT INTO assignments VALUES ('minsu', 'B전자')")
con.execute("INSERT INTO assignments VALUES ('minsu', 'C상사')")
con.execute("INSERT INTO assignments VALUES ('hana',  'C상사')")
con.execute("INSERT INTO assignments VALUES ('sora',  'C상사')")
con.execute("INSERT INTO assignments VALUES ('yuna',  'B전자')")
con.execute("INSERT INTO contracts VALUES ('C-1001', 'B전자', 'B전자 보안 점검 계약', '3,200만 원')")
con.execute("INSERT INTO contracts VALUES ('C-1002', 'C상사', 'C상사 구축 계약',     '8,500만 원')")
con.execute("INSERT INTO contracts VALUES ('C-1003', 'D물산', 'D물산 관제 위탁 계약', '1억 2,000만 원')")

con.commit()

# 잘 들어갔는지 본다.
for row in con.execute("SELECT * FROM users"):
    print(row)

con.close()