import requests

reply = requests.get('http://127.0.0.1:5100/posts/1', timeout=5)
print(reply.status_code)
print(reply.json())