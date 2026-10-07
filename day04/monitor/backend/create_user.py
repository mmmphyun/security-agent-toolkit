from werkzeug.security import generate_password_hash
from db import connect_db

# 수업용 공개 예시 계정. 기존 계정과 비밀번호를 덮어쓰지 않습니다.
password_hash = generate_password_hash("Learn123!")

with connect_db() as conn:
    result = conn.execute(
        """INSERT INTO users (username, password_hash)
           VALUES (%s, %s)
           ON CONFLICT (username) DO NOTHING""",
        ("operator", password_hash),
    )
    if result.rowcount == 1:
        print("operator 계정을 만들었습니다.")
    else:
        print("operator 계정이 이미 있습니다. 기존 계정을 유지합니다.")
