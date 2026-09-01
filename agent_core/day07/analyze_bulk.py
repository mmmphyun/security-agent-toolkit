# bulk_result.json 분석 용
import os
import json


base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "logs", "bulk_result.json")

with open(file_path, encoding="utf-8") as f:
    bulk_log = json.load(f)

# severities = {log["severity"] for log in bulk_log if "severity" in log}

severities = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}

for log in bulk_log:
    match log['severity']:
        case 'critical':
            severities['critical'] += 1
        case 'high':
            severities['high'] += 1
        case 'medium':
            severities['medium'] += 1
        case 'low':
            severities['low'] += 1
        case 'info':
            severities['info'] += 1
        case _:
            continue