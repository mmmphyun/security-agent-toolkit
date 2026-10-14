CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL
);

INSERT INTO posts (id, title, body)
VALUES (1, '첫 번째 공지', '새 프로젝트를 시작합니다.');

INSERT INTO posts (id, title, body)
VALUES (2, '실습 안내', '게시글 번호를 바꿔 보세요.');

SELECT * FROM posts;
