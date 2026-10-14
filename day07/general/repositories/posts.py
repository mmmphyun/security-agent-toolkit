from db import connect_db


def list_posts():
    with connect_db() as conn:
        return conn.execute("SELECT id, title, body FROM posts ORDER BY id").fetchall()


def find_post(post_id):
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, title, body FROM posts WHERE id = %s",
            (post_id,),
        ).fetchone()


def create_post(title, body):
    with connect_db() as conn:
        return conn.execute(
            "INSERT INTO posts (title, body) VALUES (%s, %s) RETURNING id",
            (title, body),
        ).fetchone()


def update_post(post_id, title, body):
    with connect_db() as conn:
        return conn.execute(
            "UPDATE posts SET title = %s, body = %s WHERE id = %s RETURNING id",
            (title, body, post_id),
        ).fetchone()


def delete_post(post_id):
    with connect_db() as conn:
        return conn.execute(
            "DELETE FROM posts WHERE id = %s RETURNING id", (post_id,),
        ).fetchone()
