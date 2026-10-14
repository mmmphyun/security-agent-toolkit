def validate_post(title, body):
    if not title or not body:
        return "제목과 내용을 모두 입력해 주세요."
    return None
