import requests

direct = requests.get('http://127.0.0.1:5100/posts/1', timeout=5)
via = requests.get('http://127.0.0.1:5200/posts/1', timeout=5)
same = direct.status_code == via.status_code and direct.json() == via.json()
print(direct.status_code, via.status_code, same)