# 1교시. Zero Trust 이해하기 — 회사망에 들어왔는데 왜 거절될까?

# import requests

# SERVER = "http://127.0.0.1:5001"   # 같은 PC에서 켜 둔 포털 서버

# def ask(label, user, device, health):
#     headers = {"X-User": user, "X-Device": device, "X-Device-Health": health}
#     answer = requests.get(SERVER + "/contracts/C-1001", headers=headers)
#     print(label, "->", answer.status_code, answer.json())

# ask("기준 (민수, 등록 노트북, 정상)", "minsu", "NB-0417", "ok")
# ask("A. 등록 안 된 개인 노트북   ", "minsu", "NB-9999", "ok")
# ask("B. 보안 프로그램 꺼짐       ", "minsu", "NB-0417", "off")
# ask("C. 지연의 노트북을 민수가   ", "minsu", "NB-0522", "ok")

# 2교시. 누가 확인하고 누가 막는가 — 인증과 판단 서버

import requests

SERVER = "http://127.0.0.1:5001"   # 같은 PC에서 켜 둔 포털 서버
DEVICE = "NB-0417"

def contract(headers):
    answer = requests.get(SERVER + "/contracts/C-1001", headers=headers)
    return answer.status_code, answer.json()

# 1) 지난 시간 방식 — 이름만 실어 보낸다 (사건의 요청)
print("1. 이름만 ->", contract({"X-User": "minsu", "X-Device": DEVICE, "X-Device-Health": "ok"}))

# 2) 틀린 비밀번호로 로그인
login = requests.post(SERVER + "/login", json={"user": "minsu", "password": "1234"})
print("2. 틀린 비밀번호 ->", login.status_code, login.json())

# 3) 맞는 비밀번호로 로그인하고, 받은 토큰으로 요청
login = requests.post(SERVER + "/login", json={"user": "minsu", "password": "minsu-2026"})
print("3. 로그인 ->", login.status_code, login.json())
if login.status_code != 200:
    raise SystemExit("로그인이 안 되면 여기서 멈춘다")
token = login.json()["token"]
print("   토큰으로 ->", contract({"X-Token": token, "X-Device": DEVICE, "X-Device-Health": "ok"}))

# 4) 같은 토큰, 등록 안 된 노트북
print("4. 미등록 기기 ->", contract({"X-Token": token, "X-Device": "NB-9999", "X-Device-Health": "ok"}))