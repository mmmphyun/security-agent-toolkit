import json
import requests
from flask import Flask, request
from werkzeug.security import check_password_hash
from db import connect_db

app = Flask(__name__)
app.json.ensure_ascii = False
MONITOR_URL = "http://127.0.0.1:5200/api/events"


def find_post(post_id):
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, title, body FROM posts WHERE id = %s",
            (post_id,),
        ).fetchone()


def find_user(username):
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        ).fetchone()


@app.post("/auth/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "아이디와 비밀번호를 JSON으로 보내 주세요."}, 400

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return {"error": "아이디와 비밀번호를 문자열로 보내 주세요."}, 400
    if not username.strip() or not password.strip():
        return {"error": "아이디와 비밀번호를 모두 입력해 주세요."}, 400

    user = find_user(username.strip())
    if user is None or not check_password_hash(user["password_hash"], password):
        return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, 401

    return {
        "message": "로그인 성공",
        "user": {"id": user["id"], "username": user["username"]},
    }


@app.get("/posts/<int:post_id>")
def get_post(post_id):
    post = find_post(post_id)
    if post is None:
        return {"error": "게시글을 찾을 수 없습니다."}, 404
    return post


@app.after_request
def record_request(response):
    event = {
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
    }
    print(json.dumps(event, ensure_ascii=False), flush=True)
    try:
        result = requests.post(MONITOR_URL, json=event, timeout=0.5)
        result.raise_for_status()
    except requests.RequestException:
        app.logger.warning("감시 서비스에 요청 기록을 보내지 못했습니다.")
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100)