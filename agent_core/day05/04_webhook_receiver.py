from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/")
def home():
    return "", 200

'''
Q. 대용량 로그나 실무 운영 환경에서 메모리 버퍼 방식 또는 매번 읽고 추가 후 덮어쓰기 방식이 안전해?
A. 부적합. 1번 방식 데이터 유실 위험, I/O 낭비, 메모리 고갈, 동시성 및 멀티 워커 문제.
    2번 방식 메모리 누수는 막을 수 있으나, 최악의 I/O 오버헤드가 발생. 동시 요청 발생 시 파일 락 충돌 및 데이터 오염
    => 실무 표준 방식: JSON Lines (.jsonl) 포맷 + Append 모드 ("a")
'''

recived = []
@app.route("/alert", methods=["POST"])
def alert():
    alert = request.get_json()
    recived.append(alert)

    print(f"[수신] {alert["rule"]} 경보")
    if "country" in alert:
        print(f"\t출처: {alert["country"]} ({alert["isp"]})")

    with open("./logs/received_alerts.json", "w", encoding="utf-8") as f:
        json.dump(recived, f, ensure_ascii=False, indent=2)

    return {"status": "ok"}

app.run(port=5001)