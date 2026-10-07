import json

event = {"method": "GET", "path": "/posts/999", "status_code": 404}
print(json.dumps(event, ensure_ascii=False))
