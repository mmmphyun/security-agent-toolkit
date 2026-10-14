from flask import Blueprint, request, render_template, redirect
from repositories import posts as post_repository
from post_rules import validate_post
from auth_helpers import current_user, valid_csrf

posts_bp = Blueprint("posts", __name__)


@posts_bp.get("/")
def index():
    posts = post_repository.list_posts()
    return render_template("index.html", posts=posts)


@posts_bp.get("/board/<int:post_id>")
def post_detail(post_id):
    post = post_repository.find_post(post_id)
    if post is None:
        return render_template("error.html", message="게시글을 찾을 수 없습니다."), 404
    return render_template("detail.html", post=post)


@posts_bp.route("/board/new", methods=["GET", "POST"])
def new_post():
    if current_user() is None:
        return redirect("/login", code=303)
    if request.method == "POST" and not valid_csrf(request.form.get("csrf_token")):
        return render_template("error.html", message="요청 확인 값이 올바르지 않습니다. 새로고침해 주세요."), 403

    if request.method == "GET":
        return render_template("new.html", title="", body="", error=None)

    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    error = validate_post(title, body)
    if error:
        return render_template(
            "new.html", title=title, body=body,
            error=error,
        ), 400

    post = post_repository.create_post(title, body)
    return redirect(f"/board/{post['id']}", code=303)


@posts_bp.route("/board/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    if current_user() is None:
        return redirect("/login", code=303)
    if request.method == "POST" and not valid_csrf(request.form.get("csrf_token")):
        return render_template("error.html", message="요청 확인 값이 올바르지 않습니다. 새로고침해 주세요."), 403

    post = post_repository.find_post(post_id)
    if post is None:
        return render_template("error.html", message="게시글을 찾을 수 없습니다."), 404
    if request.method == "GET":
        return render_template(
            "edit.html", post_id=post_id,
            title=post["title"], body=post["body"], error=None,
        )

    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    error = validate_post(title, body)
    if error:
        return render_template(
            "edit.html", post_id=post_id, title=title, body=body,
            error=error,
        ), 400

    updated = post_repository.update_post(post_id, title, body)
    if updated is None:
        return render_template("error.html", message="게시글을 찾을 수 없습니다."), 404
    return redirect(f"/board/{post_id}", code=303)


@posts_bp.route("/board/<int:post_id>/delete", methods=["GET", "POST"])
def delete_post(post_id):
    if current_user() is None:
        return redirect("/login", code=303)
    if request.method == "POST" and not valid_csrf(request.form.get("csrf_token")):
        return render_template("error.html", message="요청 확인 값이 올바르지 않습니다. 새로고침해 주세요."), 403

    if request.method == "GET":
        post = post_repository.find_post(post_id)
        if post is None:
            return render_template("error.html", message="게시글을 찾을 수 없습니다."), 404
        return render_template("delete.html", post=post)

    deleted = post_repository.delete_post(post_id)
    if deleted is None:
        return render_template("error.html", message="게시글을 찾을 수 없습니다."), 404
    return redirect("/", code=303)


@posts_bp.get("/posts/<int:post_id>")
def get_post(post_id):
    post = post_repository.find_post(post_id)
    if post is None:
        return {"error": "게시글을 찾을 수 없습니다."}, 404
    return post
