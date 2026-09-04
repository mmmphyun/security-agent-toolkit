# 1교시. IP 주소 파헤치기 — 32비트와 사설 주소

def is_private(ip):
    parts = ip.split(".")
    first = int(parts[0])
    second = int(parts[1])

    match first:
        case 10:
            return True
        case 172:
            if second >= 16 and second <= 31:
                return True
        case 192:
            if second == 168:
                return True
    return False

addresses = [
    "10.0.0.8",
    "172.20.5.6",
    "172.32.5.6",
    "192.168.10.25",
    "8.8.8.8",
    "203.0.113.7",
]

for address in addresses:
    if is_private(address):
        print(f"[사설] {address}")
    else:
        print(f"[공인] {address}")




'''
Q. 가정용 공유기의 NAT 설정을 켠다면 공인아이피가 하나인 환경이므로 1대의 기기만 인터넷을 사용할 수 있는건지?
A. 맞음. ISP(통신사) 회선이 단일 공인 IP만 할당(DHCP 1개 제한)하는 일반 회선이라면, 가장 먼저 IP를 할당받은 단 1대의 기기만 인터넷이 되고 나머지 기기들은 공인 IP를 받지 못해 인터넷이 끊김.
Q. PAT 환경에서 한 공인 IP에 여러 기기가 몰리면 속도 손실이 발생하는가?
A. 속도 손실이 발생하나, 포트 번호 자체의 한계 때문에 대역폭이 줄어드는 것이 아님. 공유기 하드웨어 리소스 및 물리 회선 용량에 의해 병목이 발생.
Q. 학교나 학원은 동적 NAT(1:1 풀 매핑)만 사용하는가?
A. 학교나 학원, 대규모 엔터프라이즈 환경도 순수 동적 NAT(Dynamic NAT)만 단독으로 사용하는 경우는 거의 없으며, 실제로는 "동적 PAT(Dynamic PAT, 또는 NAT Overload with IP Pool)"를 사용.
    동적 NAT를 적용했을 때 동시에 인터넷에 접속할 수 있는 단말은 정확히 254대뿐. 수백~수천 명이 이용하는 학교나 학원에서 순수 동적 NAT만 사용하는 것은 IP 자원 낭비이자 설계상 불가능.

**오해 교정**
단일 공인 IP의 가용 포트(약 64,000개)는 기기 수가 아니라 '동시 생성 가능한 L4 세션(Connection) 수'의 한계.
현대 PC나 스마트폰은 웹 페이지 하나(예: 포털 사이트, 유튜브)를 로드할 때도 백그라운드 통신, API 호출, 미디어 스트리밍 등으로 기기당 50~200개 이상의 세션을 순간적으로 사용.
공인 IP 1개로는 64,000대의 기기가 아니라 실질적으로 300~500대 정도만 접속해도 포트 고갈(Port Exhaustion) 위험에 도달.
또, 수천 명이 단 1개의 공인 IP를 공유하여 외부 서버에 동시 접속하면, 외부 보안 시스템에서는 이를 DDoS 공격, 비정상적 크롤링, 봇 트래픽으로 간주하여 CAPTCHA를 띄우거나 IP를 차단
'''