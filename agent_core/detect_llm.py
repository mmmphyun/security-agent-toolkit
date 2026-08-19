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
WORK_START = time(9, 0, 0)
WORK_END = time(18, 0, 0)

LOG_PATTERN = re.compile(
    r"(\d+:\d+:\d+).*(Failed|Accepted) password for ([\w.]+) from ([\d.]+) port (\d+)"
)


class BruteForceAlert(TypedDict):
    rule: Literal["brute_force"]
    user: str
    count: int


class PasswordSprayingAlert(TypedDict):
    rule: Literal["password_spraying"]
    ip: str
    accounts: int
    users: list[str]


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


def parse_raw_line(line: str) -> dict[str, str] | None:
    m = LOG_PATTERN.search(line)
    if m:
        return {
            "time": m.group(1),
            "event": m.group(2),
            "user": m.group(3),
            "ip": m.group(4),
            "port": m.group(5),
        }
    return None


def analyze_raw(file_path: str) -> tuple[list[dict[str, str]], int]:
    logs: list[dict[str, str]] = []
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
        return [], 0


def detect_brute_force(logs: list[dict[str, str]]) -> list[BruteForceAlert]:
    failed_users = [log["user"] for log in logs if log["event"] == "Failed"]
    counts = Counter(failed_users)

    return [
        {"rule": "brute_force", "user": user, "count": count}
        for user, count in counts.items()
        if count >= ALERT_LIMIT
    ]


def detect_password_spraying(logs: list[dict[str, str]]) -> list[PasswordSprayingAlert]:
    failed_ip_users: dict[str, set[str]] = {}
    for log in logs:
        if log["event"] == "Failed":
            ip = log["ip"]
            if ip not in failed_ip_users:
                failed_ip_users[ip] = set()
            failed_ip_users[ip].add(log["user"])

    alerts: list[PasswordSprayingAlert] = []
    for ip, users in failed_ip_users.items():
        if len(users) >= ALERT_LIMIT:
            alerts.append(
                {
                    "rule": "password_spraying",
                    "ip": ip,
                    "accounts": len(users),
                    "users": sorted(list(users)),
                }
            )
    return alerts


def detect_night_login(logs: list[dict[str, str]]) -> list[NightLoginAlert]:
    alerts: list[NightLoginAlert] = []
    for log in logs:
        if log["event"] == "Accepted":
            h, m, s = map(int, log["time"].split(":"))
            access_time = time(h, m, s)
            if access_time < WORK_START or access_time > WORK_END:
                alerts.append(
                    {
                        "rule": "night_login",
                        "time": log["time"],
                        "user": log["user"],
                        "ip": log["ip"],
                    }
                )
    return alerts


def analyze_attacks(logs: list[dict[str, str]]) -> list[Alert]:
    alerts: list[Alert] = []
    alerts.extend(detect_brute_force(logs))
    alerts.extend(detect_password_spraying(logs))
    alerts.extend(detect_night_login(logs))
    return alerts


def save_result(log_file_name: str, parsed_line: int, skipped_line: int, alerts: list[Alert]) -> None:
    combined: LogAnalysisReport = {
        "file": log_file_name,
        "parsed": parsed_line,
        "skipped": skipped_line,
        "alerts": alerts,
    }

    try:
        with open(JSON_FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logging.error(f"Failed to save JSON report: {e}")


def print_summary_report(alerts: list[Alert]) -> None:
    rule_1: list[str] = []
    rule_2: list[str] = []
    rule_3: list[str] = []

    for alert in alerts:
        match alert["rule"]:
            case "brute_force":
                rule_1.append(f"{alert['user']} — 실패 {alert['count']}회")
            case "password_spraying":
                users_str = ", ".join(alert["users"])
                rule_2.append(f"{alert['ip']} — 계정 {alert['accounts']}개 시도: [{users_str}]")
            case "night_login":
                rule_3.append(f"{alert['time']} {alert['user']} ({alert['ip']})")

    str_rule_1 = ", ".join(rule_1) if rule_1 else "없음"
    str_rule_2 = ", ".join(rule_2) if rule_2 else "없음"
    str_rule_3 = ", ".join(rule_3) if rule_3 else "없음"

    print(f"[룰 1] 확인 필요: {str_rule_1}")
    print(f"[룰 2] 의심 IP: {str_rule_2}")
    print(f"[룰 3] 심야 접속: {str_rule_3}")


def main():
    logs, skipped = analyze_raw(LOG_FILE_NAME)

    if not logs and skipped == 0:
        print("파일이 없거나 읽을 수 없습니다. 이름과 위치를 확인하세요.")
        return

    print(f"[요약] 파싱 {len(logs)}건 / 건너뜀 {skipped}건")

    alerts = analyze_attacks(logs)
    save_result(LOG_FILE_NAME, len(logs), skipped, alerts)
    print_summary_report(alerts)


if __name__ == "__main__":
    main()