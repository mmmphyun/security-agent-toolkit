import requests

body = {
    "request_id": 2,
    "approver_id": "doyun",
    "decision": "REJECTED",
    "note": "담당 부서 확인이 필요함",
}

reply = requests.post(
    "http://127.0.0.1:5002/decisions",
    json=body,
    timeout=3,
)

print(reply.status_code, reply.json())