from db import connect_db

with connect_db() as conn:
    post = conn.execute(
        "SELECT id, title, body FROM posts WHERE id = %s",
        (1,),
    ).fetchone()
    print(post)