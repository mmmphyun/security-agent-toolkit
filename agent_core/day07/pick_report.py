# 5교시. 템플릿과 LLM — 뼈대는 코드가, 살은 LLM이

import os
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "logs", "agent_result.json")

with open(file_path, encoding="utf-8") as f:
    results = json.load(f)

count = {"high": 0, "held": 0}
for r in results:
    if r["severity"] == "high":
        count['high'] += 1
    if r["result"] == "held":
        count['held'] += 1
        
print(count['high'])

warning = ""
if count['high'] > 0:
    warning += f"- **주의: high 경보 {count['high']}건 — 건별 내역을 먼저 확인할 것**"
else:
    warning += "- 특이 사항 없음"

report = f'''# 야간 보안 관제 보고

## 한눈에 보기
- 처리한 경보: 실행 {len(results)}건 (high {count['high']}건) / 보류 {count['held']}건
{warning}'''

print(report)



# <<<<<<<<<<<< 수정 시작 <<<<<<<<<<<<
# [여기를 채우기 1] high_count가 0보다 크면 경고 문구를, 아니면 "특이 사항 없음"을 warning에 담자
# [여기를 채우기 2] 제목 + 한눈에 보기 두 줄을 f-string 템플릿으로 조립해 print하자
# >>>>>>>>>>>> 수정 끝 >>>>>>>>>>>>