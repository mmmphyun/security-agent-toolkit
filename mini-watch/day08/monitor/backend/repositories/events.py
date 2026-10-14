from db import connect_db


def create_event(event):
    with connect_db() as conn:
        conn.execute(
            """INSERT INTO http_events (method, path, status_code, event_type)
               VALUES (%s, %s, %s, %s)""",
            (event["method"], event["path"], event["status_code"], event["event_type"]),
        )


def list_events(event_type):
    with connect_db() as conn:
        if event_type is None:
            rows = conn.execute("SELECT * FROM http_events ORDER BY id DESC LIMIT 50").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM http_events WHERE event_type = %s ORDER BY id DESC LIMIT 50",
                (event_type,),
            ).fetchall()
    for row in rows:
        row["occurred_at"] = row["occurred_at"].isoformat()
    return rows


def get_last_event_id():
    with connect_db() as conn:
        row = conn.execute("SELECT COALESCE(MAX(id), 0) AS id FROM http_events").fetchone()
        return row["id"]


def get_events_after(after_id, start_time=None, end_time=None):
    with connect_db() as conn:
        if start_time is not None and end_time is not None:
            rows = conn.execute(
                """SELECT id, method, path, status_code, event_type, occurred_at
                   FROM http_events
                   WHERE id > %s AND occurred_at >= %s AND occurred_at <= %s
                   ORDER BY id ASC""",
                (after_id, start_time, end_time),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, method, path, status_code, event_type, occurred_at
                   FROM http_events
                   WHERE id > %s
                   ORDER BY id ASC""",
                (after_id,),
            ).fetchall()
    for row in rows:
        row["occurred_at"] = row["occurred_at"].isoformat()
    return rows
