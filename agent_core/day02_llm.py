from collections import Counter
import logging

ALERT_LIMIT = 2
LOGS_TO_ANALYZE = "./logs/log_broken.csv"
AGENT_LOG = "agent.log"

logging.basicConfig(
    filename=AGENT_LOG,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)


def csv2dict(file: str) -> tuple[list[dict[str, str]], list[int]]:
    """CSV 파일을 읽어 파싱된 로그 리스트와 오류 라인 번호 리스트를 반환"""
    try:
        logging.info(f"파싱 시작: {file}")
        with open(file, encoding="utf-8") as f:
            keys = ["time", "user", "event", "ip"]
            lines = f.read().splitlines()

            logs = []
            errors = []

            for l_idx, line in enumerate(lines):
                try:
                    logs.append(dict(zip(keys, line.split(","), strict=True)))
                except ValueError as e:
                    errors.append(l_idx)
                    logging.warning(f"{e}, at {file}, line {l_idx} ({line or '빈 줄'})")
                    continue

            logging.info(f"{len(logs)} 줄 파싱 완료")
            return logs, errors
    except FileNotFoundError as e:
        logging.error(f"Code: {e.errno}, Message: {e.strerror}, Target: {e.filename}")
        logging.critical("비정상 종료")
        return [], []


def find_suspects(logs: list[dict[str, str]]) -> tuple[Counter, dict[str, str]]:
    """로그 내 실패 사용자 및 IP 매핑 수집"""
    failed_users = []
    failed_ip = {}

    for log in logs:
        if log["event"] == "login_failed":
            failed_users.append(log["user"])
            failed_ip[log["user"]] = log["ip"]

    return Counter(failed_users), failed_ip


def analyze_events(logs: list[dict[str, str]]) -> dict[str, int]:
    """이벤트 종류별 횟수 집계"""
    events = {"login_success": 0, "login_failed": 0, "logout": 0}

    for log in logs:
        match log["event"]:
            case "login_success":
                events["login_success"] += 1
            case "login_failed":
                events["login_failed"] += 1
            case "logout":
                events["logout"] += 1
            case _:
                logging.warning(f"UNKNOWN EVENT: {log['event']}")

    return events


def print_summary_report(
    file_path: str,
    logs: list[dict[str, str]],
    errors: list[int],
    events: dict[str, int],
    suspect_counts: Counter,
    suspect_ips: dict[str, str],
    alert_limit: int,
) -> None:
    """분석 완료된 데이터를 콘솔에 전담 출력하는 뷰 함수"""
    if errors:
        print(f"[경고] 오류 {len(errors)}회, {file_path}의 라인 {errors}")

    print(f"[요약] 정상 {len(logs)}건, 오류 {len(errors)}건")

    for event, count in events.items():
        print(f"\t{event}: {count}건")

    for user, count in suspect_counts.items():
        if count >= alert_limit:
            print(f"확인 필요: {user} — 실패 {count}회")
            print(f"\t발신 IP: {suspect_ips.get(user, 'N/A')}")


def main() -> None:
    logs, errors = csv2dict(LOGS_TO_ANALYZE)
    
    # 파싱 실패 시 처리 중단
    if not logs and errors == []:
        print("파일이 없습니다. 이름과 위치를 확인하세요")
        return

    counts, ips = find_suspects(logs)
    events = analyze_events(logs)

    # 모든 화면 출력을 리포트 전담 함수에 위임
    print_summary_report(
        file_path=LOGS_TO_ANALYZE,
        logs=logs,
        errors=errors,
        events=events,
        suspect_counts=counts,
        suspect_ips=ips,
        alert_limit=ALERT_LIMIT,
    )


if __name__ == "__main__":
    main()