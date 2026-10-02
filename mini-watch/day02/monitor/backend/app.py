import psycopg
from flask import Flask, request
from db import connect_db

app = Flask(__name__)
app.json.ensure_ascii = False


@app.get("/health")
def health():
    return {"service": "monitor", "status": "ok"}


def make_event(data):
    if not isinstance(data, dict):
        return None

    method = data.get("method")
    path = data.get("path")
    status = data.get("status_code")
    allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    if not isinstance(method, str) or method not in allowed_methods:
        return None
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        return None
    if type(status) is not int or not 100 <= status <= 599:
        return None

    if method == "POST" and path == "/auth/login" and status == 200:
        event_type = "login_success"
    elif method == "POST" and path == "/auth/login" and status == 401:
        event_type = "login_failure"
    else:
        event_type = "http_request"

    return {
        "method": method,
        "path": path,
        "status_code": status,
        "event_type": event_type,
    }


@app.post("/api/events")
def receive_event():
    event = make_event(request.get_json(silent=True))
    if event is None:
        return {"error": "method, path, status_code를 올바르게 보내 주세요."}, 400

    try:
        with connect_db() as conn:
            conn.execute(
                """INSERT INTO http_events (method, path, status_code, event_type)
                   VALUES (%s, %s, %s, %s)""",
                (event["method"], event["path"], event["status_code"], event["event_type"]),
            )
    except psycopg.Error:
        return {"error": "감시 기록을 저장할 수 없습니다."}, 503

    return {"message": "기록을 받았습니다."}, 201


@app.get("/api/events")
def get_events():
    event_type = request.args.get("event_type")
    allowed = {"login_success", "login_failure", "http_request"}
    if event_type is not None and event_type not in allowed:
        return {"error": "지원하지 않는 이벤트 종류입니다."}, 400

    try:
        with connect_db() as conn:
            if event_type is None:
                rows = conn.execute(
                    "SELECT * FROM http_events ORDER BY id DESC LIMIT 50"
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM http_events WHERE event_type = %s
                       ORDER BY id DESC LIMIT 50""",
                    (event_type,),
                ).fetchall()
    except psycopg.Error:
        return {"error": "감시 기록을 조회할 수 없습니다."}, 503

    for row in rows:
        row["occurred_at"] = row["occurred_at"].isoformat()
    return {"events": rows}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5200)