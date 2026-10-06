CREATE SEQUENCE IF NOT EXISTS posts_id_seq;

CREATE TABLE posts (
    id INTEGER PRIMARY KEY DEFAULT nextval('posts_id_seq'),
    title TEXT NOT NULL,
    body TEXT NOT NULL
);

ALTER SEQUENCE posts_id_seq OWNED BY posts.id;

INSERT INTO posts (title, body)
VALUES ('첫 번째 공지', '새 프로젝트를 시작합니다.');

INSERT INTO posts (title, body)
VALUES ('실습 안내', '게시글 번호를 바꿔 보세요.');

SELECT setval('posts_id_seq', (SELECT COALESCE(MAX(id), 0) FROM posts));

SELECT * FROM posts;
