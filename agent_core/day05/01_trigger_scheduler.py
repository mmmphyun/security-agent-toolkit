import time
import schedule
import json

'''
1교시. 트리거 — 실행 버튼을 없애는 첫걸음
'''

# alerts = [
#     {"rule": "brute_force", "severity": "high"},
#     {"rule": "night_login", "severity": "low"},
#     {"rule": "password_spraying", "severity": "high"},
# ]

# print(f"관제 데스크 시작")

# for alert in alerts:
#     if alert["severity"] == "high":
#         print(f"[호출] {alert["rule"]} — 담당자를 깨운다")
#     else:
#         print(f"[기록] {alert["rule"]} — 아침에 확인한다")
#     time.sleep(1)

# print(f"모든 경보 처리 완료")

# steps = ["로그 수집", "IP 추적", "보고서 작성"]

# print(f"점검 절차 시작")

# for i, step in enumerate(steps):
#     print(f"{i+1}/3 {step} 시작")
#     time.sleep(1)

# print(f"모든 점검 완료")

'''
3교시. schedule — 정해진 시간에 스스로

Q. 파이썬 schedule 라이브러리 schedule.every().day.at("09:00").do(check) 는 컴퓨터 또는 서버의 시간 기준이야? 따로 기준 시간대를 설정하지 않네.
    schedule.every().monday.do(check) 는 정확히 어떤 시간에 작동하는거야? 
A1. schedule.every().day.at("09:00").do(check)은 서버/컴퓨터의 로컬 시스템 시간(System Local Time) 기준.
    .at("09:00", "Asia/Seoul") 형태로 두 번째 인자에 타임존 문자열을 명시
A2. 시간을 지정하지 않으면 스크립트가 실행된(Job이 등록된) 시점의 '시:분:초'에 실행

'''

'''
Q. 콜백 함수란?
A. 다른 함수의 인자(매개변수)로 넘겨져서 나중에 실행되도록 약속된 일반 함수
'''

def process_result(now, count):
    print(f"{now} 현재 경보 {count}건")
    if count >= 4:
        print(f"[경고] 경보가 4건 이상")

'''
Q. 얘는 뭐라고 불러?
A. 고차 함수 또는 호출자 함수. 콜백 함수를 인자로 받아서 내부에서 실행
'''

def count_alerts(file, callback = None):
    with open(file, encoding="utf-8") as f:
        alerts = json.load(f)["alerts"]
        now = time.strftime("[%H:%M:%S]")
        count = len(alerts)

    if callback:
        callback(now, count)
        return None

    return now, count


schedule.every(2).seconds.do(count_alerts, file="./logs/enriched_alerts.json", callback=process_result)

while 1:
    schedule.run_pending()
    time.sleep(1)

    