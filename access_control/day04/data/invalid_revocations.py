import requests

cases = [
    ("회수 권한 없는 박지연", {"request_id": 1, "actor_id": "jiyeon", "reason": "실험"}),
    ("이미 회수한 1번 요청", {"request_id": 1, "actor_id": "doyun", "reason": "실험"}),
    ("없는 요청 번호 99", {"request_id": 99, "actor_id": "doyun", "reason": "실험"}),
    ("빈 사유", {"request_id": 2, "actor_id": "doyun", "reason": ""}),
    ("반려된 2번 요청", {"request_id": 2, "actor_id": "doyun", "reason": "실험"}),
]

for label, body in cases:
    reply = requests.post(
        "http://127.0.0.1:5002/revocations/requests",
        json=body,
        timeout=3,
    )
    print(label, reply.status_code, reply.json()["reason"])