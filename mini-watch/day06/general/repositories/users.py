from db import connect_db


def find_user(username):
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        ).fetchone()


def find_user_by_id(user_id):
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, username FROM users WHERE id = %s", (user_id,),
        ).fetchone()
