import os

import requests
from dotenv import load_dotenv

load_dotenv()                    # .env 파일을 읽어 온다 (Day 4)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"   # LLM 서비스의 창구 주소
headers = {"Authorization": "Bearer " + os.getenv("GEMINI_API_KEY"), "Content-Type": "application/json"}   # 통행증(키)을 싣는 자리

# question = input("질문: ")
'''
추가 과제
question = Aug 30 03:12:44 fw01 sshd[2201]: Failed password for admin from 185.220.101.34 port 51122 이 로그가 위험한지 평가해줘.
'''

logs = [
    "Accepted password for kim.cs from 10.0.0.12",
    "Failed password for admin from 91.240.118.172",
    "session closed for user park.js",
]

examples = """로그를 읽고 위험 또는 정상 한 단어로만 답해라.

로그: Failed password for admin from 185.220.101.34
답: 위험
로그: Accepted password for park.js from 10.0.0.31
답: 정상
"""

for i, log in enumerate(logs):
    body = {
    "model": "gemini-3.5-flash-lite",    # 어떤 모델에게
    "messages": [{"role": "user", "content": (examples + "\n" + log + "\n답: ")}],   # 무슨 말을 보낼지
    }

    response = requests.post(url, headers=headers, json=body)   # 요청을 보내고 응답을 받는다
    # print(response.status_code)                                 # 200이면 성공
    print(f"[분류] {i+1}번 로그 -> 답: {response.json()["choices"][0]["message"]["content"]}")  # 응답에서 답 문장만 꺼낸다




'''
[ 2교시 ]
Q. 현재도 프롬프트 엔지니어링이 llm 답변 퀄리티 향상에 영향을 줘?
A. 구조화 출력 강제, 표면적 휴리스틱 트릭은 구시대적. 하지만 컨텍스트 최적화, 시스템 역할 및 제약 경계 정의, 모호성 제거 및 추론 경로 유도 등
    모델에게 정확한 컨텍스트와 도메인 규칙을 주입하는 소프트웨어 인터페이스 설계 관점에서 여전히 중요함.

'''