import requests

cases = [
    {"requester_id": "ghost", "contract_id": "C-1003",
     "reason": "등록되지 않은 직원"},
    {"requester_id": "hana", "contract_id": "C-1003",
     "reason": "퇴사한 직원"},
    {"requester_id": "sora", "contract_id": "C-9999",
     "reason": "없는 계약 번호"},
    {"requester_id": "sora", "contract_id": "C-1003",
     "reason": "같은 요청 다시 보내기"},
]

for body in cases:
    reply = requests.post(
        "http://127.0.0.1:5002/requests",
        json=body,
        timeout=3,
    )
    print(reply.status_code, reply.json())
