from collections import Counter

raw_log = """02:58  kim.cs    login_success   10.1.2.11
03:02  lee.yh    login_success   10.1.2.34
03:05  park.js   login_failed    10.1.3.7
03:10  kim.cs    logout          10.1.2.11
03:11  admin     login_failed    211.45.12.9
03:12  admin     login_failed    211.45.12.9
03:14  lee.yh    logout          10.1.2.34
03:15  admin     login_failed    211.45.12.9
03:18  choi.mk   login_success   10.1.4.2
03:21  park.js   login_success   10.1.3.7
03:25  jung.hw   login_success   10.1.2.88
03:30  choi.mk   logout          10.1.4.2
03:33  song.dr   login_success   10.1.5.14
03:37  jung.hw   logout          10.1.2.88
03:40  han.sb    login_success   10.1.2.51
03:44  song.dr   logout          10.1.5.14
03:47  yoon.ka   login_success   10.1.3.29
03:50  han.sb    logout          10.1.2.51
03:52  yoon.ka   logout          10.1.3.29
03:55  park.js   logout          10.1.3.7"""

def parse_log_data(log_text):
    logs = []
    # 줄바꿈 기준으로 분할
    for line in log_text.strip().splitlines():
        # 공백이 2개 이상이든 탭이든 상관없이 연속된 공백을 기준으로 분할
        parts = line.split() 
        if len(parts) == 4:
            logs.append({
                "time": parts[0],
                "user": parts[1],
                "event": parts[2],
                "ip": parts[3]
            })
    return logs

def find_suspects(logs):
    failed_users = []

    for log in logs:
        if log["event"] == "login_failed":
            failed_users.append(log["user"])

    return failed_users

logs = parse_log_data(raw_log)
counts = Counter(find_suspects(logs))

for user, count in counts.items():
    if count >= 2:
        print(f"확인 필요: {user} — 실패 {count}회")