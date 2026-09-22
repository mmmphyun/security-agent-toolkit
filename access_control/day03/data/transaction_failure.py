import sqlite3

con = sqlite3.connect("/app/db/company.db")
con.execute("PRAGMA foreign_keys = ON")

try:
    con.execute("BEGIN")
    con.execute("""
        UPDATE access_requests
        SET status = 'APPROVED'
        WHERE request_id = 2
    """)
    con.execute("""
        INSERT INTO access_decisions (
            request_id,
            approver_id,
            decision,
            note
        )
        VALUES (2, 'ghost', 'APPROVED', '오류 시험')
    """)
    con.commit()
except sqlite3.IntegrityError:
    con.rollback()
    print("결정 저장 실패: 전체 변경을 취소했습니다.")

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
con.close()