def validate_post(title, body):
    title = (title or "").strip()
    body = (body or "").strip()
    if not title or not body:
        return title, body, "제목과 내용을 모두 입력해 주세요."
    return title, body, None
