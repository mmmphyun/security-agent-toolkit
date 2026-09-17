# 서버부: 요청 값을 검사한 뒤, 허용된 요청에만 계약서를 돌려준다.
import json
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False  # 응답의 한글을 그대로 표시

# 메모장으로 저장한 UTF-8 회사 파일을 딕셔너리로 읽는다.
with open("company.json", encoding="utf-8-sig") as file:
    company = json.load(file)

CONTRACT_ID = "C-1001"   # 제공할 계약서 번호
ALLOWED_USER = "minsu"  # 이번 실습에서 허용할 요청 값


@app.get("/document")  # GET /document 요청이 들어오면 실행
def document():
    # request: 현재 받은 요청. args: 주소의 ? 뒤에 담긴 값들
    # ?user=minsu → "minsu". user를 안 보내면 빈 문자열을 사용한다.
    user = request.args.get("user", "")

    if user != ALLOWED_USER:  # 지정한 값과 다르면 계약서를 주지 않는다.
        print(f"[DENY] user={user}", flush=True)
        return {"result": "DENY", "reason": "허용 대상이 아닙니다"}, 403

    # company 전체 → contracts → 계약서 번호에 해당하는 딕셔너리
    contract = company["contracts"][CONTRACT_ID]
    print(f"[ALLOW] user={user} contract={CONTRACT_ID}", flush=True)
    return {
        "result": "ALLOW",
        "title": contract["title"],
        "amount": contract["amount"]
    }, 200


if __name__ == "__main__":
    # 컨테이너 밖에서 전달되는 요청도 받는다. 입력할 접속 주소는 아니다.
    app.run(host="0.0.0.0", port=5000, debug=False)
