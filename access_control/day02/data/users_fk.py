import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

con.execute("""
    CREATE TABLE users_new (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        employed INTEGER NOT NULL,
        FOREIGN KEY (role) REFERENCES roles(role)
    )
""")

con.execute("""
    INSERT INTO users_new
    SELECT *
    FROM users
""")
con.execute("DROP TABLE users")
con.execute("ALTER TABLE users_new RENAME TO users")
con.commit()

for row in con.execute("""
    SELECT *
    FROM users
"""):
    print(row)

con.close()