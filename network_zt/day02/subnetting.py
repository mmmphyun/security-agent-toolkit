# 3교시. 서브네팅 계산 — 필요한 만큼 정확히 나누기

import ipaddress

assignments = [
    ("개발팀", "10.20.0.0/26"),
    ("운영팀", "10.20.0.64/27"),
    ("보안팀", "10.20.0.96/28"),
]

for name, cidr in assignments:
    network = ipaddress.ip_network(cidr)
    hosts = list(network.hosts())
    first_host = hosts[0]
    last_host = hosts[-1]
    usable = network.num_addresses - 2
    print(f"{name} {network} {first_host}~{last_host} {usable}대")




'''
Q. 서브네팅에 FLSM과 VLSM이 있다 배웠어.
    FLSM은 이후 다른 서브넷 그룹을 추가할 때 기존 서브넷을 만지지 않고 뒤에 그대로 붙일 수 있어서 좋아보이고,
    VLSM은 주소 공간 효율성이 좋아보이지만, 요구량이 큰 순서대로 정렬되어야 하니 이후에 다른 서브넷 그룹을 추가할 때 기존 서브넷 그룹까지 건드려야하는 부분이 아쉬워보여.
    실제로 이렇게 평가되는지, 실무에서는 어떤 상황에 어떻게 나누어서 사용하는지 궁금해.
A. VLSM을 사용하는 실무에서는 새로운 대규모 그룹이 생긴다고 해서 이미 운영 중인 서버, 스위치, 방화벽의 IP를 전부 재할당(Re-addressing)하는 일은 절대 하지 않음.
    초기 설계 단계에서 미리 계층적 IP 블록(예: 개발/운영/관리망, 가용영역별)을 나누고, 각 영역 뒤쪽에 예약(Reserved) 블록을 남겨두는 방식으로 VLSM을 구현.
    예측 범위를 완전히 벗어나는 대규모 확장이 필요하면 기존 대역을 엎는 것이 아니라, 상위 라우터에 새로운 Supernet(CIDR 블록)을 추가 할당.
    FLSM의 경우 비용과 주소 고갈 문제가 치명적. 공인 IP나 엔터프라이즈 환경에서는 감당하기 힘든 낭비.

    따라서, 오늘날 모든 라우팅 프로토콜(OSPFv2/v3, BGP, EIGRP)과 클라우드 인프라(AWS VPC, GCP VPC, Azure VNet)는 기본적으로 VLSM/CIDR 기반으로 설계.

    실무에서는 최상위 단계에서의 관리 편의를 위해 규모별 표준 모듈(FLSM 방식)로 큼직하게 쪼갠 후
    그 할당된 블록 내부에서는 용도(P2P 링크, 웹 서버, DB 서버, 관리망)에 맞춰 가변 서브넷(VLSM 방식)으로 쪼개어 IP 낭비를 막고 라우팅 테이블을 요약.
'''