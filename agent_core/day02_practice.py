from collections import Counter
import logging

ALERT_LIMIT = 2                        # 확인 필요 기준: 실패 횟수
LOGS_TO_ANALYZE = "./logs/log_broken.csv"    # 분석할 로그 파일
AGENT_LOG = "agent.log"


logging.basicConfig(
    filename=AGENT_LOG,                              # 기록을 남길 파일
    level=logging.INFO,                                # INFO 이상을 기록한다
    format="%(asctime)s %(levelname)s %(message)s",    # 시각 심각도 내용 순서로
    encoding="utf-8",
)

def csv2dict(file: str) -> List[Dict[str, str]]:
    try:
        logging.info(f"파싱 시작: {file}")
        with open(file, encoding = "utf-8") as f:
            keys = ["time", "user", "event", "ip"]
            lines = f.read().splitlines()

            logs = []
            errors = []

            for l in range(len(lines)):
                try:
                    logs.append(dict(zip(keys, lines[l].split(","), strict = True)))
                except ValueError as e:
                    errors.append(l)
                    logging.warning(f"{e}, at {file}, line {l} ({lines[l] or '빈 줄'})")
                    continue

            if errors is not None:
                print(f"[경고] 오류 {len(errors)}회, {file}의 라인 {errors}")

            logging.info(f"{len(logs)} 줄 파싱 완료")
            print(f"[요약] 정상 {len(logs)}건, 오류 {len(errors)}건")
            return logs
    except FileNotFoundError as e:
        logging.error(f"Code: {e.errno}, Message: {e.strerror}, Target: {e.filename}")
        print("파일이 없습니다. 이름과 위치를 확인하세요")
        logging.critical(f"비정상 종료")
        return []

def find_suspects(logs: List[Dict[str, str]]) -> Tuple[Dict[str, int], Dict[str, str]]:
    failed_users = []
    failed_ip = {}

    for log in logs:
        if log["event"] == "login_failed":
            failed_users.append(log["user"])
            failed_ip[log["user"]] = log["ip"]

    return Counter(failed_users), failed_ip

def analyze_events(logs: List[Dict[str, str]]) -> Dict[str, int]:
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

def main():
    logs = csv2dict(LOGS_TO_ANALYZE)
    counts, ips = find_suspects(logs)
    events = analyze_events(logs)

    for event, count in events.items():
        print(f"\t{event}: {count}건")

    for user, count in counts.items():
        if count >= ALERT_LIMIT:
            print(f"확인 필요: {user} — 실패 {count}회")
            print(f"\t발신 IP: {ips[user]}")

if __name__ == "__main__":
    main()
    