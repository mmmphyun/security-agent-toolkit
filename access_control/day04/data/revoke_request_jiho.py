import requests

body = {
    "request_id": 1,
    "actor_id": "doyun",
    "reason": "C상사 장애 대응 종료",
}

reply = requests.post(
    "http://127.0.0.1:5002/revocations/requests",
    json=body,
    timeout=3,
)

print(reply.status_code, reply.json())