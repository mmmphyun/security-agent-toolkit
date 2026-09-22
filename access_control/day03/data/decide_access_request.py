import os
import sqlite3

DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")


def decide_access_request(request_id, approver_id, decision, note):
    decision = decision.upper()
    if decision not in ("APPROVED", "REJECTED"):
        return "UNKNOWN_DECISION"

    con = sqlite3.connect(DB_FILE)
    con.execute("PRAGMA foreign_keys = ON")

    try:
        con.execute("BEGIN")

        permission = con.execute("""
            SELECT 1
            FROM users
            JOIN permissions
            ON users.role = permissions.role
            WHERE users.user_id = ?
            AND users.employed = 1
            AND permissions.action = 'approve_access_requests'
        """, (approver_id,)).fetchone()
        if permission is None:
            con.rollback()
            return "NO_APPROVAL_PERMISSION"

        request_row = con.execute("""
            SELECT requester_id, status
            FROM access_requests
            WHERE request_id = ?
        """, (request_id,)).fetchone()
        if request_row is None:
            con.rollback()
            return "UNKNOWN_REQUEST"
        if request_row[0] == approver_id:
            con.rollback()
            return "SELF_APPROVAL_NOT_ALLOWED"
        if request_row[1] != "PENDING":
            con.rollback()
            return "ALREADY_DECIDED"

        con.execute("""
            UPDATE access_requests
            SET status = ?
            WHERE request_id = ?
        """, (decision, request_id))
        con.execute("""
            INSERT INTO access_decisions (
                request_id,
                approver_id,
                decision,
                note
            )
            VALUES (?, ?, ?, ?)
        """, (request_id, approver_id, decision, note))

        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    return "RECORDED"