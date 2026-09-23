import sqlite3

LOG_FILE = "/app/logs/pdp.log.1"

rows = []
with open(LOG_FILE, encoding="utf-8") as file:
    for line in file:
        date, time, tag, user, contract, decision, reason = line.split()
        rows.append((
            date + " " + time,
            user.split("=")[1],
            contract.split("=")[1],
            decision,
            reason,
        ))

con = sqlite3.connect("/app/db/company.db")
existing = set(con.execute("""
    SELECT logged_at, user_id, contract_id
    FROM access_log
"""))
new_rows = [row for row in rows if (row[0], row[1], row[2]) not in existing]
con.executemany("""
    INSERT INTO access_log (
        logged_at, user_id, contract_id, decision, reason
    )
    VALUES (?, ?, ?, ?, ?)
""", new_rows)
con.commit()
con.close()

print(f"{len(new_rows)}줄을 access_log에 넣었습니다. (이미 있던 줄 {len(rows) - len(new_rows)}줄은 건너뜀)")