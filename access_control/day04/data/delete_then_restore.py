import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    DELETE FROM assignments
    WHERE user_id = 'sora'
    AND customer = 'B전자'
""")
con.commit()
print("지운 뒤:")
for row in con.execute("SELECT * FROM assignments"):
    print(" ", row)

con.execute("""
    INSERT INTO assignments (user_id, customer)
    VALUES ('sora', 'B전자')
""")
con.commit()
print("되돌린 뒤:")
for row in con.execute("SELECT * FROM assignments"):
    print(" ", row)

con.close()