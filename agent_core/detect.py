import re
import json
import logging
from collections import Counter
from datetime import time
from typing import Literal, TypedDict

ALERT_LIMIT = 2
FILE_PATH = "./logs/"
LOG_FILE_NAME = FILE_PATH + "sample_server.log"
JSON_FILE_NAME = FILE_PATH + "alerts.json"
WORK_START = time(9,0,0)
WORK_END = time(18,0,0)

class BruteForceAlert(TypedDict):
    rule: Literal["brute_force"]
    user: str
    count: int


class PasswordSprayingAlert(TypedDict):
    rule: Literal["password_spraying"]
    ip: str
    accounts: int


class NightLoginAlert(TypedDict):
    rule: Literal["night_login"]
    time: str
    user: str
    ip: str


type Alert = BruteForceAlert | PasswordSprayingAlert | NightLoginAlert


class LogAnalysisReport(TypedDict):
    file: str
    parsed: int
    skipped: int
    alerts: list[Alert]


def parse_raw_line(line: str) -> list[dict[str, str]] | None:
    pattern = r"(\d+:\d+:\d+).*(Failed|Accepted) password for ([\w.]+) from ([\d.]+) port (\d+)"
    m = re.search(pattern, line)

    if m:
        return {
            "time": m.group(1),
            "event": m.group(2),
            "user": m.group(3),
            "ip": m.group(4),
            "port": m.group(5)
        }
    return m

def analyze_raw(file_path: str) -> tuple[list[dict[str]], int]:
    logs: list[dict[str]] = []
    skipped: int = 0

    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                log = parse_raw_line(line)
                if log:
                    logs.append(log)
                else:
                    skipped += 1

        return logs, skipped
    except FileNotFoundError as e:
        logging.error(f"Code: {e.errno}, Message: {e.strerror}, Target: {e.filename}")
        return

def analyze_attacks(logs: list[dict[str]]) -> list[Alert]:
    failed_users: list[str] = []
    failed_ip: dict[str, set[str]] = {}
    alert: list[Alert] = []
    ip: str = ""

    for log in logs:
        # rule_1, rule_2
        if log["event"] == "Failed":
            # rule_1
            failed_users.append(log["user"])

            # rule_2
            if log["ip"] not in failed_ip:
                failed_ip[log["ip"]] = set()
            failed_ip[log["ip"]].add(log["user"])

        # rule_3
        elif log["event"] == "Accepted":
            parts = log["time"].split(":")
            access_time = time(int(parts[0]), int(parts[1]), int(parts[2]))
            if access_time < WORK_START or access_time > WORK_END:
                alert.append({"rule": "night_login", "time": log["time"], "user": log["user"], "ip": log["ip"]})

    counts = Counter(failed_users)
    for user, count in counts.items():
        if count >= ALERT_LIMIT:
            alert.append({"rule": "brute_force", "user": user, "count": count})

    for ip, user in failed_ip.items():
        if len(user) >= ALERT_LIMIT:
            alert.append({"rule": "password_spraying", "ip": ip, "accounts": len(user), "users": list(user)})

    return alert

def save_result(log_file_name: str, parsed_line: int, skipped_line: int, alerts: Alert) -> None:
    combined = {
        "file": log_file_name,
        "parsed": parsed_line,
        "skipped": skipped_line,
        "alerts": alerts
    }

    try:
        with open(JSON_FILE_NAME, "w", encoding = "utf-8") as f:
            json.dump(combined, f, ensure_ascii = False, indent = 2)
    except:
        return

def print_summary_report(alerts: Alert) -> None:
    rule_1 = []
    rule_2 = []
    rule_3 = []

    for alert in alerts:
        match alert["rule"]:
            case "brute_force":
                rule_1.append(f"{alert["user"]} — 실패 {alert["count"]}회")
            case "password_spraying":
                rule_2.append(f"{alert["ip"]} — 계정 {alert["accounts"]}개 시도: {alert["users"]}")
            case "night_login":
                rule_3.append(f"{alert["time"]} {alert["user"]} ({alert["ip"]})")
    
    print("[룰 1] 확인 필요: " + ", ".join(rule_1))
    print("[룰 2] 의심 IP: " + ", ".join(rule_2))
    print("[룰 3] 심야 접속: " + ", ".join(rule_3))


def main():
    logs, skipped = analyze_raw(LOG_FILE_NAME)

    if not logs:
        print("파일이 없습니다. 이름과 위치를 확인하세요")
        return

    print(f"[요약] 파싱 {len(logs)}건 / 건너뜀 {skipped}건")

    alerts = analyze_attacks(logs)
    save_result(LOG_FILE_NAME, len(logs), skipped, alerts)
    print_summary_report(alerts)


if __name__ == "__main__":
    main()