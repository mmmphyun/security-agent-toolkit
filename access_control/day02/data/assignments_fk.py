import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    CREATE TABLE assignments_new (
        user_id TEXT NOT NULL,
        customer TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
""")

con.execute("""
    INSERT INTO assignments_new
    SELECT *
    FROM assignments
""")
con.execute("DROP TABLE assignments")
con.execute("ALTER TABLE assignments_new RENAME TO assignments")
con.commit()

for row in con.execute("""
    SELECT *
    FROM assignments
"""):
    print(row)

con.close()