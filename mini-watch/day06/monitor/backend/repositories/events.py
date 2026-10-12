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
