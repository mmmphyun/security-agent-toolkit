import requests

BASE = "http://127.0.0.1:5100"

response = requests.post(
    f"{BASE}/auth/login",
    json={"username": "student", "password": "Wrong123!"},
    timeout=5,
)
print("로그인 실패", response.status_code)
response = requests.post(
    f"{BASE}/auth/login",
    json={"username": "student", "password": "Learn123!"},
    timeout=5,
)
print("로그인 성공", response.status_code)
print("게시글 조회", requests.get(f"{BASE}/posts/1", timeout=5).status_code)
print("없는 게시글", requests.get(f"{BASE}/posts/999", timeout=5).status_code)
