# 1교시. 오리엔테이션 — 네트워크를 배우는 이유와 첫 관찰

import subprocess

targets = ["192.168.0.1", "8.8.8.8", "google.com", "192.0.2.1"]   # 첫 값은 내 게이트웨이 주소로
print(f"아침 점검 시작 — 대상 {len(targets)}개")

for target in targets:
    return_code = subprocess.run(["ping", "-n", "1", "-w", "1000", "8.8.8.8"], capture_output=True)

    if return_code == 0:
        print(f"[OK] {target}")
    else:
        print(f"[응답 없음] {target}")



# LIMIT = 100                          # 이 값(ms)을 넘으면 느리다고 보는 기준

# results = [
#     {"target": "naver.com", "time": 4, "ttl": 54},
#     {"target": "google.com", "time": 34, "ttl": 115},
#     {"target": "8.8.8.8", "time": 34, "ttl": 115},
# ]

# for r in results:
#     if r["time"] > LIMIT:            # 기준과 비교해 판정한다
#         grade = "[느림]"
#     else:
#         grade = "[정상]"
#     print(f"{grade} {r['target']:<12} {r['time']:>4}ms  TTL={r['ttl']}")   # 서식 지정 — 1과목에서 배운 그것


'''
이번 과목은 이론 중심.
학과에서 전공으로 배운 네트워크 관련 개념임.
따라서 코드 실습은 적음.
'''