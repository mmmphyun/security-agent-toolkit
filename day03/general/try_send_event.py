import requests

response = requests.post(
    "http://127.0.0.1:5200/api/events",
    json={"method": "GET", "path": "/posts/1", "status_code": 200},
    timeout=5,
)
print("기록 전송", response.status_code)
print(response.json())
