import requests

requests.post(
    "http://127.0.0.1:5001/alert",
    json={"rule": "brute_force", "severity": "high"},
)
requests.post(
    "http://127.0.0.1:5001/alert",
    json={"rule": "night_login", "severity": "low"},
)