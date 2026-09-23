import os
import sqlite3

DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")


def revoke_assignment(user_id, customer, actor_id, reason):
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
            AND permissions.action = 'revoke_access'
        """, (actor_id,)).fetchone()
        if permission is None:
            con.rollback()
            return "NO_REVOKE_PERMISSION"

        row = con.execute("""
            SELECT 1
            FROM assignments
            WHERE user_id = ?
            AND customer = ?
        """, (user_id, customer)).fetchone()
        if row is None:
            con.rollback()
            return "UNKNOWN_ASSIGNMENT"

        con.execute("""
            DELETE FROM assignments
            WHERE user_id = ?
            AND customer = ?
        """, (user_id, customer))

        con.execute("""
            INSERT INTO access_changes (
                target_kind,
                target_key,
                action,
                actor_id,
                reason
            )
            VALUES ('assignment', ?, 'REVOKE', ?, ?)
        """, (user_id + "/" + customer, actor_id, reason))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return "RECORDED"


def revoke_request(request_id, actor_id, reason):
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
            AND permissions.action = 'revoke_access'
        """, (actor_id,)).fetchone()
        if permission is None:
            con.rollback()
            return "NO_REVOKE_PERMISSION"

        row = con.execute("""
            SELECT status
            FROM access_requests
            WHERE request_id = ?
        """, (request_id,)).fetchone()
        if row is None:
            con.rollback()
            return "UNKNOWN_REQUEST"
        if row[0] != "APPROVED":
            con.rollback()
            return "NOT_APPROVED"

        con.execute("""
            UPDATE access_requests
            SET status = 'REVOKED'
            WHERE request_id = ?
        """, (request_id,))

        con.execute("""
            INSERT INTO access_changes (
                target_kind,
                target_key,
                action,
                actor_id,
                reason
            )
            VALUES ('request', ?, 'REVOKE', ?, ?)
        """, (str(request_id), actor_id, reason))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return "RECORDED"