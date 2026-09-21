import sqlite3

con = sqlite3.connect("/app/db/company.db")

for row in con.execute("""
    SELECT *
    FROM assignments
"""):
    print(row)

con.close()