-- general_db에서 실행합니다. 일반 서버를 멈춘 뒤 적용합니다.
-- 기존 테이블과 자료를 보존하며, 새 DB에서도 실행할 수 있습니다.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL
);
CREATE SEQUENCE IF NOT EXISTS posts_id_seq;
ALTER TABLE posts ALTER COLUMN id SET DEFAULT nextval('posts_id_seq');
SELECT setval('posts_id_seq', GREATEST(
    (SELECT COALESCE(MAX(id), 0) FROM posts),
    (SELECT last_value FROM posts_id_seq)
));
