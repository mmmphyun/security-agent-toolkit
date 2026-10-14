from db import connect_db

with connect_db() as conn:
    event = conn.execute(
        """INSERT INTO http_events (method, path, status_code, event_type)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        ("GET", "/posts/1", 200, "http_request"),
    ).fetchone()
    row = conn.execute(
        "SELECT id, method, path, status_code, event_type FROM http_events WHERE id = %s",
        (event["id"],),
    ).fetchone()
    print(row)
