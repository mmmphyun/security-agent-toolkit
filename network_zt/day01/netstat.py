# 3교시. OSI 7계층 알아보기 (2) — 위쪽 네 층과 장애 좁히기

LINES = """TCP    192.168.0.15:51234     93.184.216.34:443      ESTABLISHED
TCP    192.168.0.15:51240     172.217.161.238:443    ESTABLISHED
TCP    192.168.0.15:51255     13.107.42.16:443       ESTABLISHED
TCP    192.168.0.15:51261     23.76.153.112:80       ESTABLISHED
TCP    192.168.0.15:51288     20.42.65.92:443        ESTABLISHED"""

PORTS = {80: "HTTP", 443: "HTTPS", 53: "DNS", 22: "SSH"}

counts = {}
for line in LINES.split("\n"):
    parts = line.split()
    remote = parts[2]                    # 세 번째 칸이 외부 주소다
    port = int(remote.split(":")[1])     # 콜론 뒤가 포트 번호
    if port in counts:
        counts[port] = counts[port] + 1
    else:
        counts[port] = 1

for port in counts:
    if port in PORTS:
        name = PORTS[port]
    else:
        name = "모르는 포트"
    print(f"{port} ({name}) — {counts[port]}개")