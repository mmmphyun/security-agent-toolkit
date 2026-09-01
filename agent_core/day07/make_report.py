# 1교시. 보고서 형식 — 마크다운과 파일 저장

import os
from datetime import date

today = date.today()                 # 오늘 날짜
print(today)

report = f'''# {today}

- 처리한 경보: 0건
'''

# folder = f"reports/{str(today)[:7]}"
# os.makedirs(folder, exist_ok=True)

# with open(f"{folder}/daily_report_{today}.md", "w", encoding="utf-8") as f:
#     f.write(report)
#     print(f"[완료] {f.name} 저장")

base_dir = os.path.dirname(os.path.abspath(__file__)) # 동적 절대경로 생성
folder = os.path.join(base_dir, "reports", today.strftime("%Y-%m")) # OS별 경로 구분자 이슈 방지 + 표준 날짜 포맷터 사용
os.makedirs(folder, exist_ok=True)

file_path = os.path.join(folder, f"daily_report_{today}.md")
with open(file_path, "w", encoding="utf-8") as f:
    f.write(report)
    print(f"[완료] {f.name} 저장")

'''
Q. 상대경로의 개념
A. 코드 파일의 위치가 아니라 터미널의 현재 작업 디렉터리
    os.path.abspath(__file__)을 이용한 절대경로 사용 방식으로 수정
'''