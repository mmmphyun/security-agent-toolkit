import requests


domains = [
    "http://ip-api.com/json/8.8.8.8",
    "http://no-such-host-abc123.invalid",
    "https://httpbin.org/delay/10"
]

for domain in domains:
    try:
        response = requests.get(domain, timeout=3)
        print(domain, "→", response.status_code)
    except requests.exceptions.Timeout:
        print(domain, "→ 응답 시간 초과")
    except requests.exceptions.ConnectionError:
        print(domain, "→ 연결 실패")

     