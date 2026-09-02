# 2교시. 알림 연동 — 실패해도 멈추지 않게
# 6교시. 종합 실습 — 완성과 회고

from flask import Flask, request

app = Flask(__name__)

@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json()
    print(f"[수신] {data['rule']}")
    return {"result": "ok"}

app.run(port=5001)