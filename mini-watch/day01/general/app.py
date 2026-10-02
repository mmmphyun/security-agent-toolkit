from flask import Flask

app = Flask(__name__)
app.json.ensure_ascii = False  # JSON 응답의 한글을 그대로 표시

POSTS = {
    1: {"id": 1, "title": "첫 번째 공지", "body": "일반 서비스를 준비합니다."},
    2: {"id": 2, "title": "실습 안내", "body": "게시글 번호를 바꿔 보세요."},
}
@app.get('/posts/<int:post_id>')
def get_post(post_id):
    post = POSTS.get(post_id)
    if post is None:
        return {'error': 'POST_NOT_FOUND'}, 404
    return post, 200