from flask import Flask, request
import json

'''
4교시. Flask — 받는 쪽이 되기
'''

app = Flask(__name__)

@app.route("/")
def home():
    return "관제 데스크 가동 중"

@app.route("/status")
def status():
    with open("./logs/enriched_alerts.json", encoding="utf-8") as f:
        alerts = json.load(f)["alerts"]
        count = len(alerts)

    return {"desk": "가동 중", "alerts": count}

@app.route("/hello/<name>")
def hello(name):
    return f"{name} 님, 관제 데스크에 온 것을 환영한다"

@app.route("/help")
def available_address():
    routes = [rule.rule for rule in app.url_map.iter_rules() if rule.endpoint != "static"]
    return f"available_routes: {routes}"

'''
Q. 하드코딩해서 다 넣는 방법 말고 다른 방법이 있을까?
A. Flask 애플리케이션에 등록된 모든 라우트(Endpoint 및 URL 규칙)는 하드코딩할 필요 없이 app.url_map을 순회하여 동적으로 추출
'''

@app.route("/rules")
def rules():
    result = []
    with open("./logs/enriched_alerts.json", encoding="utf-8") as f:
        alerts = json.load(f)["alerts"]

        for alert in alerts:
            result.append(alert["rule"])

    return {"rules": result}

'''
5교시. POST와 웹훅 — 경보 배달
'''

@app.route("/alert", methods=["POST"])
def alert():
    data = request.get_json()
    if data["severity"] == "high":
        print(f"[긴급] {data["rule"]}")
    else:
        print(f"[일반] {data["rule"]}")

    '''
    Q. 플라스크 내 각 라우터 함수는 무조건 리턴값이 존재해야해?
    A. Flask의 모든 라우트(뷰) 함수는 반드시 유효한 응답 객체 또는 응답으로 변환 가능한 값을 반환
    - 반환할 데이터가 없는 경우 204 No Content
    '''
    return "", 204


app.run(port=5001)