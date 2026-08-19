import requests
import json
from collections import Counter

def extract_alerts_with_ip(json_file: str):
    alerts = []
    lookup = {}
    try:
        with open(json_file, encoding="utf-8") as f:
            json2dict = json.load(f)
            alerts = json2dict["alerts"]
        
        for i, alert in enumerate(alerts):
            if "ip" in alert:
                lookup = lookup_ip(alert["ip"])

                alert["country"] = lookup["country"]
                alert["isp"] = lookup["isp"]

                alerts[i] = alert

        json2dict["alerts"] = alerts

        return json2dict, alerts
    except FileNotFoundError:
        return []

def lookup_ip(ip: str):
    response = requests.get(f"http://ip-api.com/json/{ip}")
    data = response.json()
    if data["status"] == "success":
        return {"country": data["country"], "isp": data["isp"]}
    return None

def print_summary_report(alerts):
    for alert in alerts:
        if "ip" in alert:
            print(f"[추적] {alert["ip"]} -> {alert["country"]} ({alert["isp"]})")

def save_result(json2dict):
    try:
        with open("enriched_alerts.json", "w", encoding="utf-8") as f:
            f = json.dump(json2dict, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        pass


def main():
    json2dict, alerts = extract_alerts_with_ip("./logs/alerts.json")
    print_summary_report(alerts)
    save_result(json2dict)


if __name__ == "__main__":
    main()
