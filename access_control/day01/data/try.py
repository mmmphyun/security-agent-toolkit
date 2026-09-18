import sqlite3

con = sqlite3.connect("/app/db/company.db")

con.execute("INSERT INTO users VALUES ('short', '짧음', 'sales')")
con.commit()

con.close()