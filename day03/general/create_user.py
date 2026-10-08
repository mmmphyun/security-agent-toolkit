from werkzeug.security import generate_password_hash
from db import connect_db

password_hash = generate_password_hash("Learn123!")

with connect_db() as conn:
    result = conn.execute(
        """INSERT INTO users (username, password_hash)
           VALUES (%s, %s)
           ON CONFLICT (username) DO NOTHING""",
        ("student", password_hash),
    )
    if result.rowcount == 1:
        print("student 계정을 만들었습니다.")
    else:
        print("student 계정이 이미 있습니다. 기존 계정을 유지합니다.")
