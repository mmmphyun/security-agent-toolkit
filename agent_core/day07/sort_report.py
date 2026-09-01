# 3교시. 우선순위 정렬 — 위험한 것부터

import os
import json

RANK = {"high": 0, "medium": 1, "low": 2}   # 작을수록 앞으로

def sort_key(r):                     # r = 판단 한 건 (딕셔너리)
    severity = r["severity"]         # 심각도 글자를 꺼내서
    if severity in RANK:
        return RANK[severity]            # 점수로 바꿔 돌려준다
    return 99


base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "logs", "agent_result.json")

with open(file_path, encoding="utf-8") as f:
    results = json.load(f)

results = sorted(results, key=sort_key)

for i, r in enumerate(results):
    print(f"{i:<3} {r['severity']:<8} {r['tool']:<14} →    {r['result']}")

