import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


def load_alerts_data(file_path: Path) -> Dict[str, Any]:
    """JSON 파일로부터 알림 데이터를 로드한다."""
    with open(file_path, mode="r", encoding="utf-8") as f:
        return json.load(f)


def save_alerts_data(file_path: Path, data: Dict[str, Any]) -> None:
    """가공된 알림 데이터를 JSON 파일로 저장한다."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_ip_info(ip: str) -> Optional[Dict[str, str]]:
    """외부 API를 통해 단일 IP의 국가 및 ISP 정보를 조회한다."""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            return {"country": data["country"], "isp": data["isp"]}
    except (requests.RequestException, KeyError):
        pass
    return None


def enrich_alert_with_ip(alert: Dict[str, Any]) -> Dict[str, Any]:
    """단일 알림 객체에 IP 조회 정보를 결합한다."""
    ip = alert.get("ip")
    if not ip:
        return alert

    ip_info = fetch_ip_info(ip)
    if ip_info:
        alert["country"] = ip_info["country"]
        alert["isp"] = ip_info["isp"]
        alert["lookup_success"] = True
    else:
        alert["lookup_success"] = False

    return alert


def enrich_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """전체 알림 목록의 IP 정보를 보강한다."""
    return [enrich_alert_with_ip(alert) for alert in alerts]


def print_summary_report(alerts: List[Dict[str, Any]]) -> None:
    """보강된 알림 데이터의 처리 결과를 요약 출력한다."""
    for alert in alerts:
        ip = alert.get("ip")
        if not ip:
            continue

        if alert.get("lookup_success"):
            print(f"[추적] {ip} -> {alert['country']} ({alert['isp']})")
        else:
            print(f"[실패] {ip} -> IP 정보 조회 실패")


def main() -> None:
    input_path = Path("./logs/alerts.json")
    output_path = Path("enriched_alerts.json")

    try:
        data = load_alerts_data(input_path)
    except FileNotFoundError:
        print(f"[오류] 입력 파일을 찾을 수 없습니다: {input_path}")
        return

    alerts = data.get("alerts", [])
    enriched_alerts = enrich_alerts(alerts)
    data["alerts"] = enriched_alerts

    print_summary_report(enriched_alerts)
    save_alerts_data(output_path, data)


if __name__ == "__main__":
    main()