import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from db import connect_db

DATA = Path(__file__).parent / "data"


def read_json(name):
    path = DATA / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def parse_time(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def last_event_id():
    with connect_db() as conn:
        row = conn.execute("SELECT COALESCE(MAX(id), 0) AS id FROM http_events").fetchone()
        return row["id"]


def live_events(after_id, seconds=60, reference_at=None):
    now = reference_at or datetime.now(timezone.utc)
    if isinstance(now, str):
        now = parse_time(now)
    start_time = now - timedelta(seconds=seconds)
    with connect_db() as conn:
        rows = conn.execute(
            """SELECT id, method, path, status_code, event_type, occurred_at
               FROM http_events
               WHERE id > %s AND occurred_at >= %s AND occurred_at <= %s
               ORDER BY id ASC""",
            (after_id, start_time, now),
        ).fetchall()
    for row in rows:
        row["occurred_at"] = row["occurred_at"].isoformat()
    return rows, now.isoformat()
