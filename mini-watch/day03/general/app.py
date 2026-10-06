from flask import Flask, request, render_template
from werkzeug.security import check_password_hash
from db import connect_db
from routes.posts import posts_bp
from repositories.posts import find_post
from request_logging import init_request_logging

app = Flask(__name__)
app.json.ensure_ascii = False

app.register_blueprint(posts_bp)
init_request_logging(app)


@app.get("/login")
def login_page():
    return render_template("login.html")


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100)