import sqlite3

DB_FILE = "/app/db/company.db"

with sqlite3.connect(DB_FILE) as con:
    con.execute("""
        UPDATE access_requests
        SET status = 'APPROVED'
        WHERE request_id = 2
    """)

try:
    with sqlite3.connect(DB_FILE) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("""
            INSERT INTO access_decisions (
                request_id,
                approver_id,
                decision,
                note
            )
            VALUES (2, 'ghost', 'APPROVED', '오류 시험')
        """)
except sqlite3.IntegrityError:
    print("결정 저장 실패: 요청 상태만 남았습니다.")

with sqlite3.connect(DB_FILE) as con:
    status = con.execute("""
        SELECT status
        FROM access_requests
        WHERE request_id = 2
    """).fetchone()[0]
    decision_count = con.execute("""
        SELECT COUNT(*)
        FROM access_decisions
        WHERE request_id = 2
    """).fetchone()[0]

print("2번 요청 상태:", status)
print("2번 결정 수:", decision_count)