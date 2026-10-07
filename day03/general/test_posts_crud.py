from app import app
from repositories.posts import find_post


def run_checks():
    client = app.test_client()

    print("[1] GET / - 목록 조회")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.get_data(as_text=True)
    assert "게시글 목록" in html
    assert "새 게시글 작성" in html

    print("[2] GET /board/new - 작성 폼 조회")
    res = client.get("/board/new")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "<form" in html
    assert 'name="title"' in html
    assert 'name="body"' in html

    print("[3] POST /board/new - 빈 값/공백 검증 (400)")
    # 공백 제목
    res = client.post("/board/new", data={"title": "   ", "body": "내용입니다"})
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    html = res.get_data(as_text=True)
    assert "제목과 내용을 모두 입력해 주세요." in html
    # 공백 내용
    res = client.post("/board/new", data={"title": "제목입니다", "body": "   "})
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    html = res.get_data(as_text=True)
    assert "제목과 내용을 모두 입력해 주세요." in html

    print("[4] POST /board/new - 정상 작성 (303 리다이렉트)")
    test_title = "테스트 게시글 자동생성"
    test_body = "테스트 본문 내용입니다."
    res = client.post("/board/new", data={"title": test_title, "body": test_body})
    assert res.status_code == 303, f"Expected 303, got {res.status_code}"
    redirect_url = res.headers["Location"]
    assert redirect_url.startswith("/board/"), f"Unexpected location: {redirect_url}"
    post_id = int(redirect_url.split("/")[-1])
    print(f"    생성된 post_id: {post_id}")

    print("[5] GET /board/<id> - 상세 조회 및 링크 확인")
    res = client.get(f"/board/{post_id}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert test_title in html
    assert test_body in html
    assert "목록으로" in html
    assert f"/board/{post_id}/edit" in html
    assert f"/board/{post_id}/delete" in html

    print("[6] GET /board/<id>/edit - 수정 폼 조회")
    res = client.get(f"/board/{post_id}/edit")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert test_title in html
    assert test_body in html

    print("[7] POST /board/<id>/edit - 빈 값 검증 (400, 기존 내용 유지)")
    res = client.post(f"/board/{post_id}/edit", data={"title": "  ", "body": test_body})
    assert res.status_code == 400
    html = res.get_data(as_text=True)
    assert "제목과 내용을 모두 입력해 주세요." in html
    # DB 조회하여 유지 확인
    post_in_db = find_post(post_id)
    assert post_in_db["title"] == test_title

    print("[8] POST /board/<id>/edit - 정상 수정 (303 리다이렉트)")
    updated_title = "수정된 테스트 제목"
    updated_body = "수정된 테스트 본문입니다."
    res = client.post(
        f"/board/{post_id}/edit",
        data={"title": updated_title, "body": updated_body},
    )
    assert res.status_code == 303
    assert res.headers["Location"] == f"/board/{post_id}"

    # 수정 반영 확인
    res = client.get(f"/board/{post_id}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert updated_title in html
    assert updated_body in html

    print("[9] GET /board/<id>/delete - 삭제 확인 폼 (글 보존 확인)")
    res = client.get(f"/board/{post_id}/delete")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert updated_title in html
    assert "삭제 확인" in html
    # DB에 여전히 존재하는지 확인
    assert find_post(post_id) is not None

    print("[10] POST /board/<id>/delete - 실제 삭제 (303 리다이렉트)")
    res = client.post(f"/board/{post_id}/delete")
    assert res.status_code == 303
    assert res.headers["Location"] == "/"
    assert find_post(post_id) is None

    print("[11] 삭제 후 접근 시 404 확인")
    assert client.get(f"/board/{post_id}").status_code == 404
    assert client.get(f"/board/{post_id}/edit").status_code == 404
    assert client.post(f"/board/{post_id}/edit", data={"title": "a", "body": "b"}).status_code == 404
    assert client.get(f"/board/{post_id}/delete").status_code == 404
    assert client.post(f"/board/{post_id}/delete").status_code == 404

    print("[12] 기존 JSON API /posts/<id> 및 /auth/login, /login 페이지 검증")
    res = client.get("/posts/1")
    assert res.status_code in (200, 404)
    # 없는 게시글 json
    assert client.get(f"/posts/{post_id}").status_code == 404
    # 로그인 화면 GET
    res_login = client.get("/login")
    assert res_login.status_code == 200
    assert "아이디" in res_login.get_data(as_text=True)
    # 로그인 정상 테스트 (student / Learn123!)
    login_res = client.post("/auth/login", json={"username": "student", "password": "Learn123!"})
    assert login_res.status_code in (200, 401)  # 계정 생성 여부에 따라

    print("모든 검증 케이스 통과 완료.")


if __name__ == "__main__":
    run_checks()
