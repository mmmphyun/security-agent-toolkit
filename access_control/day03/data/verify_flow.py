import requests

cases = [
    ("jiho", "C-1002", 200, {"result", "title", "amount"}),
    ("jiho", "C-1001", 403, {"result", "reason"}),
    ("sora", "C-1003", 403, {"result", "reason"}),
    ("minsu", "C-1002", 200, {"result", "title", "amount"}),
    ("jiyeon", "C-1003", 200, {"result", "amount"}),
    ("hana", "C-1002", 403, {"result", "reason"}),
]

for user, contract_id, expected_status, expected_fields in cases:
    reply = requests.get(
        "http://pep:5000/document",
        params={"user": user, "contract": contract_id},
        timeout=3,
    )
    body = reply.json()
    assert reply.status_code == expected_status
    assert set(body) == expected_fields
    print("PASS", user, contract_id, reply.status_code)