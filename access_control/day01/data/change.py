import sqlite3

con = sqlite3.connect("/app/db/company.db")

for row in con.execute("SELECT contract_id, amount, amount_won FROM contracts"):
    print("전:", row)

con.execute("UPDATE contracts SET amount_won = 32000000 WHERE contract_id = 'C-1001'")
con.execute("UPDATE contracts SET amount_won = 85000000 WHERE contract_id = 'C-1002'")
con.execute("UPDATE contracts SET amount_won = 120000000 WHERE contract_id = 'C-1003'")
con.commit()

for row in con.execute("SELECT contract_id, amount, amount_won FROM contracts"):
    print("후:", row)

con.close()