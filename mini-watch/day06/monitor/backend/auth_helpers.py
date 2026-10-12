import hmac
import os
import secrets

from flask import request, session
from repositories import users as user_repository


def configure_session(app, cookie_name):
    secret_key = os.environ.get("SECRET_KEY", "")
    if len(secret_key) < 32 or secret_key.startswith("CHANGE_ME"):
        raise RuntimeError(".env의 SECRET_KEY를 직접 생성한 32자 이상의 값으로 설정해 주세요.")
    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_NAME=cookie_name,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,  # 로컬 HTTP 실습. HTTPS 배포에서는 True.
    )


def current_user():
    user_id = session.get("user_id")
    if type(user_id) is not int:
        return None
    user = user_repository.find_user_by_id(user_id)
    if user is None:
        session.pop("user_id", None)
    return user


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def valid_csrf(token):
    expected = session.get("csrf_token")
    return (
        isinstance(token, str)
        and isinstance(expected, str)
        and hmac.compare_digest(token.encode("utf-8"), expected.encode("utf-8"))
    )


def api_access_error():
    if current_user() is None:
        return {"error": "로그인이 필요합니다."}, 401
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if not valid_csrf(request.headers.get("X-CSRF-Token")):
            return {"error": "요청 확인 값이 올바르지 않습니다. 새로고침 후 다시 시도해 주세요."}, 403
    return None


def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def template_auth():
    return {"login_user": current_user(), "csrf_token": csrf_token()}
