CREATE SEQUENCE IF NOT EXISTS posts_id_seq;

ALTER TABLE posts ALTER COLUMN id SET DEFAULT nextval('posts_id_seq');

SELECT setval('posts_id_seq', GREATEST(
    (SELECT COALESCE(MAX(id), 0) FROM posts),
    (SELECT last_value FROM posts_id_seq)
));
