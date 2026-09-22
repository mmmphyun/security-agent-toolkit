import requests

body = {
    "requester_id": "sora",
    "contract_id": "C-1003",
    "reason": "D물산 계약 검토 지원",
}

reply = requests.post(
    "http://127.0.0.1:5002/requests",
    json=body,
    timeout=3,
)

print(reply.status_code, reply.json())