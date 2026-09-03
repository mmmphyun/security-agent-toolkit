# 4교시. TCP와 UDP, 그리고 3-way, 4way Handshake

# packets = [
#     {"no": 12, "src": "192.168.0.15", "dst": "93.184.216.34", "flags": ["SYN"]},
#     {"no": 13, "src": "93.184.216.34", "dst": "192.168.0.15", "flags": ["SYN", "ACK"]},
#     {"no": 14, "src": "192.168.0.15", "dst": "93.184.216.34", "flags": ["ACK"]},
#     {"no": 15, "src": "192.168.0.15", "dst": "168.126.63.1", "flags": []},
#     {"no": 16, "src": "192.168.0.15", "dst": "93.184.216.34", "flags": ["ACK"]},
# ]

# print("[SYN 필터]")
# for packet in packets:
#     if "SYN" in packet['flags']:
#         print(f"{packet['no']} {packet['src']} → {packet['dst']} {packet['flags']}")

# print("[서버 대화 필터]")
# server = "93.184.216.34"
# for packet in packets:
#     if packet['src'] == server or packet['dst'] == server:
#         print(f"{packet['no']} {packet['src']} → {packet['dst']} {packet['flags']}")

packets = [
    {"src": "192.168.0.15", "dst": "93.184.216.34", "flags": ["SYN"]},
    {"src": "10.0.0.99", "dst": "192.168.0.15", "flags": ["SYN"]},
    {"src": "10.0.0.99", "dst": "192.168.0.15", "flags": ["SYN"]},
    {"src": "93.184.216.34", "dst": "192.168.0.15", "flags": ["SYN", "ACK"]},
    {"src": "10.0.0.99", "dst": "192.168.0.15", "flags": ["SYN"]},
]

counts = {}
for p in packets:
    if "SYN" in p["flags"] and "ACK" not in p["flags"]:   # 순수 SYN만 골라서
        src = p["src"]
        if src not in counts:            # 처음 보는 IP면 0으로 시작 (1과목 카운팅 패턴)
            counts[src] = 0
        counts[src] = counts[src] + 1

for ip in counts:
    if counts[ip] >= 3:
        print(f"[의심] {ip} — 답장 없는 SYN {counts[ip]}개")
    else:
        print(f"[정상] {ip} — 답장 없는 SYN {counts[ip]}개")