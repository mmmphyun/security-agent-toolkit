import requests
import json


def json2dict(json_file_path):
    with open(json_file_path, encoding="utf-8") as f:
        data = json.load(f)
        alerts = data["alerts"]

    return alerts

def send_alert(dest, alert):
    response = requests.post(dest, json=alert)
    
    return response

def print_console(rule, response):
    print(f"[전송] {rule} -> {response.json()['status']}")

def main():
    alerts = json2dict("./logs/enriched_alerts.json")

    for alert in alerts:
        response = send_alert("http://127.0.0.1:5001/alert", alert)
        print_console(alert["rule"], response)


if __name__ == "__main__":
    main()