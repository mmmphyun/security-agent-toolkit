from db import connect_db


def list_notes():
    with connect_db() as conn:
        return conn.execute("SELECT id, title, body FROM notes ORDER BY id").fetchall()


def find_note(note_id):
    with connect_db() as conn:
        return conn.execute("SELECT id, title, body FROM notes WHERE id = %s", (note_id,)).fetchone()


def create_note(title, body):
    with connect_db() as conn:
        return conn.execute(
            "INSERT INTO notes (title, body) VALUES (%s, %s) RETURNING id, title, body",
            (title, body),
        ).fetchone()


def update_note(note_id, title, body):
    with connect_db() as conn:
        return conn.execute(
            "UPDATE notes SET title = %s, body = %s WHERE id = %s RETURNING id, title, body",
            (title, body, note_id),
        ).fetchone()


def delete_note(note_id):
    with connect_db() as conn:
        return conn.execute("DELETE FROM notes WHERE id = %s RETURNING id", (note_id,)).fetchone()
