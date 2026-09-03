# 2교시. OSI 7계층 알아보기 (1) — 아래쪽 세 층

import re

def is_ip(address):
    parts = address.split(".")           # 점 기준으로 마디를 나눈다

    if len(parts) != 4:
        return False

    for part in parts:
        try:
            if int(part) < 0 and int(part) > 255:
                return False
        except:
            return False
    
    return True                          # 검사를 전부 통과했으면 IP다

MAC_HYPHEN_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$") # 맥 주소 유효성 검증을 위해 정규식 도입

def is_mac(address):
    parts = address.split("-")

    if len(parts) != 6:
        return False

    return bool(MAC_HYPHEN_PATTERN.fullmatch(address.strip()))


addresses = ["192.168.0.15", "A4-B1-C2-D3-E4-F5", "8.8.8.8", "300.1.1.1", "AA-BB-CC"]
for address in addresses:
    if is_ip(address):
        print(f"[IP] {address}")
    elif is_mac(address):
        print(f"[MAC] {address}")
    else:
        print(f"[정체불명] {address}")




'''
Q. (MAC 주소 유효성 검증을 위해 질문하다 만난 개념 질문) MAC 주소의 논리적 제약 항목엔 무엇이 있지?
A. (1) I/G (Individual / Group) 비트: 유니캐스트 vs 멀티캐스트: 첫 번째 옥텟(최상위 바이트)의 최하위 비트(Bit 0, LSB)는 해당 주소가 단일 장비를 가리키는지, 특정 그룹을 가리키는지를 결정
        - Unicast (I/G = 0) / Multicast (I/G = 1)
    (2) U/L (Universally / Locally Administered) 비트: 제조사 할당 vs 로컬 생성: 첫 번째 옥텟의 두 번째 최하위 비트(Bit 1)는 주소의 발급 및 보장 체계를 의미
        - UAA (Universally Administered Address, U/L = 0) / LAA (Locally Administered Address, U/L = 1)
    (3) 특수 목적 및 예약 주소 (Special & Reserved Addresses): 특정 용도로 사전에 예약되어 있어 일반 장비에 고유 할당할 수 없는 주소 형태
        - Broadcast Address (FF-FF-FF-FF-FF-FF) / Null / Zero Address (00-00-00-00-00-00) / 프로토콜 전용 제어 주소
    (4) OUI (Organizationally Unique Identifier) 기반 제조사 검증: 상위 3바이트(24비트)를 IEEE 공인 OUI 데이터베이스와 대조하는 방식. 인가된 벤더의 단말만 네트워크에 접속하도록 통제하는 화이트리스트/블랙리스트 정책에 사용

    단순 유효성 검증 API라면 널 주소, 브로드캐스트, 멀티캐스트 정도만 기본 차단 대상으로 두는 것이 일반적.
'''