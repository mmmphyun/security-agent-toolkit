# 3교시. OSI 7계층 알아보기 (2) — 위쪽 네 층과 장애 좁히기

def diagnose(checks):
    if checks["wifi"] == False:
        return "1~2층 문제 — 케이블·Wi-Fi 연결부터 확인"
    if checks["gateway"] == False:
        return "내 방 문제 — 공유기를 확인"
    if checks["internet"] == False:
        return "외부 회선 문제 — 통신사 쪽 확인"
    if checks["dns"] == False:
        return "이름 풀이 문제 — DNS 설정 확인"
    return "정상"

scenarios = [
    {"name": "1번 PC", "wifi": True, "gateway": True, "internet": True, "dns": False},
    {"name": "2번 PC", "wifi": True, "gateway": True, "internet": True, "dns": True},
    {"name": "3번 PC", "wifi": False, "gateway": False, "internet": False, "dns": False},
    {"name": "4번 PC", "wifi": True, "gateway": True, "internet": True, "dns": True},
    {"name": "5번 PC", "wifi": True, "gateway": False, "internet": False, "dns": False},
]

normal = 0
abnormal = 0

for s in scenarios:
    result = diagnose(s)
    if result == "정상":
        normal += 1
    else:
        abnormal += 1
        print(f"[점검 필요] {s['name']} - {result}")

print(f"정상 {normal}대 / 점검 필요 {abnormal}대")