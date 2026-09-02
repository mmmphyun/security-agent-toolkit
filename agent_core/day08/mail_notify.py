# 2교시. 알림 연동 — 실패해도 멈추지 않게

import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()
msg = MIMEText("야간 보고서가 생성되었습니다.")
msg["Subject"] = "[관제] 야간 보고 완료"
msg["From"] = os.getenv("MAIL_USER")
msg["To"] = os.getenv("MAIL_USER")          # 나에게 보낸다 — 도착을 내 눈으로 확인

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:      # 메일 서버에 연결해
    server.login(os.getenv("MAIL_USER"), os.getenv("MAIL_PASSWORD"))   # 로그인하고 (키는 .env에 — Day 4 철칙)
    server.send_message(msg)                                 # 보낸다
print("[알림] 이메일 발송 완료")