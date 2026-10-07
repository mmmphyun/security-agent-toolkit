import psycopg
from flask import request, render_template
from werkzeug.exceptions import HTTPException


def http_error(error):
    if request.path.startswith("/api/"):
        messages = {404: "요청한 주소를 찾을 수 없습니다.", 405: "지원하지 않는 요청 방법입니다."}
        return {"error": messages.get(error.code, "요청을 처리할 수 없습니다.")}, error.code
    return error


def database_error(error):
    if request.path.startswith("/api/") or request.path.startswith("/auth/"):
        return {"error": "DB에 연결할 수 없습니다. 서버의 DB 설정을 확인해 주세요."}, 503
    return {"error": "DB 연결 상태를 확인해 주세요."}, 503


def register_error_handlers(app):
    app.register_error_handler(HTTPException, http_error)
    app.register_error_handler(psycopg.Error, database_error)
