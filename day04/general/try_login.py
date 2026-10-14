import requests

URL = "http://127.0.0.1:5100/auth/login"
cases = [
    ("정상 로그인", {"username": "student", "password": "Learn123!"}),
    ("잘못된 비밀번호", {"username": "student", "password": "Wrong123!"}),
    ("없는 아이디", {"username": "nobody", "password": "Learn123!"}),
    ("빠진 비밀번호", {"username": "student"}),
]

for label, data in cases:
    response = requests.post(URL, json=data, timeout=5)
    print(label, response.status_code, response.json())
