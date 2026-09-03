# 6교시. 종합 실습 — 패킷 분석 보고서

packets = [
    {"src": "192.168.100.249", "dst": "104.20.23.154", "info": "[SYN]"},
    {"src": "104.20.23.154", "dst": "192.168.100.249", "info": "[SYN, ACK]"},
    {"src": "192.168.100.249", "dst": "104.20.23.154", "info": "[ACK]"},
]

headers = [
    {"item": "출발지 IP", "value": "192.168.100.249", "where": "IP 헤더 (3층)"},
    {"item": "목적지 IP", "value": "104.20.23.154", "where": "IP 헤더 (3층)"},
    {"item": "TTL", "value": "128", "where": "IP 헤더 (3층)"},
    {"item": "출발지 포트", "value": "51234", "where": "TCP 헤더 (4층)"},
    {"item": "목적지 포트", "value": "443", "where": "TCP 헤더 (4층)"},
    {"item": "플래그", "value": "SYN", "where": "TCP 헤더 (4층)"},
]


print("| 순서 | Source | Destination | Info |")
print("|---|---|---|---|")
for i, packet in enumerate(packets):
    print(f"| {i} | {packet['src']} | {packet['dst']} | {packet['info']} |")

print()

print("| 항목 | 값 | 어느 헤더 |")
print("|---|---|---|")
for header in headers:
    print(f"| {header['item']} | {header['value']} | {header['where']} |")