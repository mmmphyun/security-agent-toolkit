---
title: "주소의 설계와 네트워크 격리 — CIDR·서브네팅과 VLAN·Inter-VLAN 라우팅 아키텍처"
slug: "c02-network-zt-day02"
description: "IPv4 32비트 구조와 사설 IP 판별, ipaddress 모듈 기반 VLSM 가변 서브네팅, 그리고 Cisco Packet Tracer를 활용한 VLAN 2계층 하드 격리 및 3계층 Inter-VLAN 라우팅 실증"
pubDate: 2026-09-04
tags: ["Network", "Subnetting", "CIDR", "VLAN", "Routing", "Packet Tracer", "Zero Trust"]
category: "네트워크·Zero Trust"
status: "published"
---

## 1. 개요 및 학습 개념 요약

[이전 포스트](/security-agent-toolkit/blog/c02-network-zt-day01/)에서는 패킷의 캡슐화 구조와 OSI 7계층 장애 격리 사다리, 그리고 TCP 핸드셰이크 상태 머신을 분석했다. 상위 애플리케이션의 단순한 네트워크 호출 이면에는 물리 계층부터 전송 계층까지 이어지는 복잡한 패킷 제어 흐름이 존재함을 확인했다.

하지만 네트워크 인터페이스가 유효하더라도, 조직 내 모든 단말이 단일 대역에 무질서하게 묶여 있다면 심각한 보안 위협이 발생한다. 업무용 PC, 내부 핵심 데이터베이스, 복도의 CCTV가 동일한 브로드캐스트 도메인에 방치될 경우, 비인가 도청이나 횡적 이동 공격에 무방비로 노출된다.

> 단일 물리 네트워크 안에서 데이터 흐름을 안전하게 통제하려면 논리적 IP 분할과 물리적 세그먼트 격리가 상호 보완적으로 맞물려야 한다.

주소 체계를 체계적으로 재설계하고 제로 트러스트 관점의 경계 분리를 달성하기 위해 32비트 IPv4 주소 체계와 서브네팅, 그리고 VLAN 기반의 네트워크 분리 아키텍처를 설계했다. 파이썬 스크립트로 주소 판별과 서브넷 속성 추출을 자동화하고, 시뮬레이터를 통해 패킷 전달 경로를 실증했다.

- **32비트 IPv4 주소 구조와 사설망 식별:** 4개 옥텟을 비트 단위로 분석하고 RFC 1918 표준 사설 IP 대역을 결정론적으로 판별하는 로직을 구현했다.
- **CIDR 표기법과 가변 서브네팅:** 고정 크기 분할의 주소 낭비를 극복하기 위해 `ipaddress` 모듈을 활용하여 조직 규모에 맞춘 가변 길이 서브넷을 설계했다.
- **2계층 스위칭과 3계층 라우팅 분기 판단:** 동일 VLAN 내부의 로컬 통신과 이종 네트워크 간 게이트웨이 경유 통신을 구분하는 경로 결정 엔진을 도출했다.
- **Cisco Packet Tracer 기반 세그멘테이션 실증:** 2960 스위치와 2911 라우터를 배치하여 VLAN 10과 VLAN 20 간의 2계층 프레임 차단 및 3계층 Inter-VLAN 라우팅을 검증했다.

## 2. 전체 산출물 및 네트워크 세그멘테이션 아키텍처

당일 실습에서는 파이썬 기반의 주소 분석 엔진 4종과 Cisco Packet Tracer 기반의 인프라 토폴로지를 구축했다. 각 산출물이 담당하는 네트워크 계층과 격리 메커니즘은 다음과 같다.

| 산출물 | 대상 계층 | 핵심 파일 및 장비 | 주요 역할 및 설정 내용 | 네트워크 격리 및 경로 제어 방식 |
|---|---|---|---|---|
| 사설 IP 판별기 | L3 (네트워크) | `network_zt/day02/check_ip.py` | 32비트 옥텟 파싱, 사설 대역 3종 매칭 | 공인 IP와 사설 IP를 분리하여 외부 직접 노출 차단 |
| 서브넷 속성 요약기 | L3 (네트워크) | `network_zt/day02/subnet_mask.py` | CIDR 파싱, 네트워크 및 브로드캐스트 주소 연산 | 서브넷 마스크 비트 연산을 통한 로컬 통신 경계 정의 |
| 가변 서브네팅 엔진 | L3 (네트워크) | `network_zt/day02/subnetting.py` | 부서별 필요 호스트 수 기반 가변 길이 분할 | 주소 낭비 최소화 및 부서별 IP 블록 격리 |
| 통신 경로 결정 엔진 | L2/L3 복합 | `network_zt/day02/route.py` | VLAN ID 및 네트워크 대역 일치 여부 판정 | 동일 VLAN 직접 전달 대 라우터 게이트웨이 분기 |
| 패킷 트레이서 토폴로지 | L2/L3 인프라 | `day2_lesson5_vlan_router_verified.pkt` | Cisco 2960 Switch, Cisco 2911 Router | IEEE 802.1Q 포트 태깅 및 Inter-VLAN 라우팅 |

## 3. 기존 체계의 한계와 도전 과제

통신사로부터 단일 C클래스 사설 대역을 할당받아 모든 기기를 단일 스위치에 연결하는 기존 플랫 네트워크 구성은 치명적인 보안 취약점을 내포한다.

개발팀 PC, 운영팀 서버, 외부 게스트 단말, 사내 폐쇄회로 카메라가 동일한 브로드캐스트 도메인에 묶여 있으면, 단일 호스트의 악성코드 감염이 전체 내부망으로 확산된다.

> 플랫 네트워크 환경에서는 브로드캐스트 프레임이 모든 포트로 플러딩되므로, 악의적 단말이 ARP 스푸핑을 시도할 경우 전체 세션의 기밀성이 손상된다.

또한 L3 서브넷 마스크만으로 대역을 나누는 방식은 2계층 수준의 실질적 격리를 제공하지 못한다. 동일한 물리 스위치에 연결된 단말이 네트워크 카드에 보조 IP를 수동 할당하거나 무차별 모드를 활성화하면, 서로 다른 서브넷 간의 트래픽도 도청할 수 있다.

마지막으로 고정 크기 서브네팅을 사용할 경우 소규모 팀에도 대규모 주소 블록이 할당되어 심각한 IP 낭비가 발생한다. 외부 통신을 위한 NAT 환경에서도 단일 공인 IP의 64,000개 포트 자원은 동시 L4 커넥션 폭증 시 급격히 고갈되어 통신 장애를 유발한다.

## 4. 엔지니어링 의사결정 및 네트워크 설계

### 4.1. 32비트 사설 IP 식별과 PAT 세션 고갈 방어 로직 (`check_ip.py`)

네트워크 경계 보안의 첫 단계는 외부 인터넷 통신 대상과 내부 인트라넷 통신 대상을 식별하는 것이다. `check_ip.py`에서는 점 표기법 문자열을 정수형 옥텟으로 분해한 뒤, 구조적 패턴 매칭으로 RFC 1918 사설망 규격을 검증하도록 구현했다.

```python
# network_zt/day02/check_ip.py
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
```

사설 IP 대역은 `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`의 세 가지로 한정된다. 단순하게 첫 번째 옥텟이 172라는 이유만으로 사설 주소로 오판하는 결함을 방지하기 위해, 두 번째 옥텟의 범위를 16부터 31까지 엄격하게 검증했다.

사설망 내부 단말이 외부와 통신할 때 공유기나 방화벽은 포트 주소 변환(PAT) 기술을 사용한다. 이때 공인 IP 1개가 제공하는 약 64,000개의 포트는 연결 가능한 단말의 대수가 아니라 동시 활성 L4 세션 수의 상한선이다.

현대 웹 브라우저와 백그라운드 프로세스는 단말당 수십에서 수백 개의 세션을 동시에 생성한다. 따라서 수백 대 규모의 엔터프라이즈 환경에서는 단일 공인 IP 대신 복수의 공인 IP 풀을 기반으로 한 동적 PAT를 설계해야 세션 고갈 및 외부 보안 장비의 차단을 방지할 수 있다.

### 4.2. ipaddress 모듈 기반 서브넷 속성 자동 추출과 VLSM 주소 할당 (`subnet_mask.py`, `subnetting.py`)

서브넷 마스크는 32비트 주소 체계에서 네트워크 식별자와 호스트 식별자의 경계선을 정의하는 비트 필터다. `subnet_mask.py`에서는 파이썬 표준 라이브러리인 `ipaddress`를 활용하여 CIDR 블록으로부터 필수 네트워크 파라미터를 추출하는 함수를 작성했다.

```python
# network_zt/day02/subnet_mask.py
import ipaddress

def summarize_subnet(cidr):
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = list(network.hosts())
    summary = {}

    summary['network'] = str(network.network_address)
    summary['broadcast'] = str(network.broadcast_address)
    summary['first_host'] = hosts[0]
    summary['last_host'] = hosts[-1]
    summary['usable'] = network.num_addresses - 2
    
    return summary
```

호스트 비트가 모두 0인 주소는 네트워크 식별용으로 예약되고, 모두 1인 주소는 해당 세그먼트의 전체 브로드캐스트용으로 예약된다. 따라서 실제 단말에 할당 가능한 유효 호스트 수는 전체 주소 개수에서 2를 차감한 `network.num_addresses - 2`가 된다.

기존의 고정 길이 서브네팅은 모든 서브넷에 균일한 호스트 비트를 부여하므로 자원 낭비가 크다. 이를 해결하기 위해 `subnetting.py`에서는 필요한 호스트 수에 따라 프리픽스 길이를 차등 적용하는 가변 길이 서브네팅(VLSM)을 도입했다.

```python
# network_zt/day02/subnetting.py
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
```

개발팀에는 62대 수용이 가능한 `/26` 블록을, 운영팀에는 30대 수용의 `/27` 블록을, 보안팀에는 14대 수용의 `/28` 블록을 순차적으로 배정했다.

실무 인프라 환경에서는 새로운 대규모 그룹이 추가된다고 해서 운영 중인 장비의 IP를 전면 재할당할 수 없다. 초기 설계 단계에서 계층적 블록 뒤편에 예약 공간을 사전에 확보하고, 최상위 표준 모듈과 내부 가변 블록을 결합하는 하이브리드 아키텍처를 수립해야 한다.

### 4.3. L2 로컬 포워딩과 L3 기본 게이트웨이 경로 결정 엔진 (`route.py`)

네트워크 단말이 목적지 IP로 패킷을 전송할 때, 로컬 스위치를 통한 직접 전달인지 라우터 게이트웨이를 경유해야 하는지 판단하는 알고리즘이 필요하다. `route.py`에서는 출발지와 목적지의 VLAN ID 및 서브넷 네트워크 객체를 비교하여 경로를 판정하는 엔진을 구축했다.

```python
# network_zt/day02/route.py
import ipaddress

devices = {
    "PC0": {"vlan": 10, "ip": "192.168.10.10/26", "gateway": "192.168.10.1"},
    "PC1": {"vlan": 10, "ip": "192.168.10.20/26", "gateway": "192.168.10.1"},
    "PC2": {"vlan": 20, "ip": "192.168.10.70/26", "gateway": "192.168.10.65"},
}

def decide_path(source, destination, router_exists):
    source_info = devices[source]
    destination_info = devices[destination]
    source_network = ipaddress.ip_interface(source_info["ip"]).network
    destination_network = ipaddress.ip_interface(destination_info["ip"]).network

    if source_info["vlan"] == destination_info["vlan"] and source_network == destination_network:
        return "스위치 직접 전달"
    if router_exists:
        return f"게이트웨이 {source_info['gateway']}로 전달"

    return "통신 불가"
```

출발지와 목적지가 동일한 VLAN ID를 공유하고 IP 서브넷이 일치하면, 라우터의 개입 없이 스위치 MAC 학습 테이블 기반의 로컬 포워딩이 수행된다.

반면 VLAN이 다르거나 목적지 서브넷이 상이한 경우, 단말은 자신의 서브넷 내부에 존재하는 기본 게이트웨이 주소로 프레임을 전송해야 한다. 만약 중계할 라우터가 존재하지 않는다면 패킷은 목적지에 도달하지 못하고 통신 불가 상태로 격리된다.

### 4.4. Cisco Packet Tracer 기반 VLAN 분리와 Inter-VLAN 라우팅 토폴로지 실증 (`packet_tracer.md`)

소프트웨어적인 IP 서브넷 분할의 한계를 극복하고 물리적 2계층 하드 격리를 달성하기 위해, Cisco Packet Tracer 9.0.1 환경에서 스위치와 라우터를 연동한 실증 망을 구성했다.

Cisco 2960 스위치에 VLAN 10과 VLAN 20을 독립적으로 생성하고, 각 부서 단말이 연결된 물리 포트를 해당 VLAN의 액세스 포트로 격리 배정했다.

```python
Switch(config)# vlan 10
Switch(config-vlan)# name DEV
Switch(config-vlan)# exit
Switch(config)# vlan 20
Switch(config-vlan)# name SEC
Switch(config-vlan)# exit
Switch(config)# interface range fastethernet 0/1 - 2
Switch(config-if-range)# switchport mode access
Switch(config-if-range)# switchport access vlan 10
Switch(config-if-range)# exit
Switch(config)# interface range fastethernet 0/3 - 4
Switch(config-if-range)# switchport mode access
Switch(config-if-range)# switchport access vlan 20
```

스위치 포트 격리 직후 라우터가 없는 상태에서 통신을 검증했다. 동일한 VLAN 10에 속한 PC0에서 PC1로의 핑은 100% 성공했으나, VLAN 20에 속한 PC2로의 핑은 100% 패킷 손실을 기록하며 완벽한 통신 단절을 입증했다.

```text
C:\> ping 192.168.10.20
192.168.10.20: Sent = 4, Received = 4, Lost = 0 (0% loss)

C:\> ping 192.168.20.10
192.168.20.10: Sent = 4, Received = 0, Lost = 4 (100% loss)
```

이후 두 격리 망 간의 합법적 통신을 중계하기 위해 Cisco 2911 라우터를 투입하고, 스위치의 Fa0/5 포트를 VLAN 10, Fa0/6 포트를 VLAN 20에 연결하여 라우터의 G0/0 및 G0/1 인터페이스와 결합했다.

```python
Router(config)# interface gigabitethernet 0/0
Router(config-if)# ip address 192.168.10.1 255.255.255.0
Router(config-if)# no shutdown
Router(config-if)# exit
Router(config)# interface gigabitethernet 0/1
Router(config-if)# ip address 192.168.20.1 255.255.255.0
Router(config-if)# no shutdown
```

각 PC의 기본 게이트웨이를 라우터 인터페이스 IP로 지정한 뒤 다시 핑을 전송한 결과, 이종 VLAN 간 통신이 지연 없이 성공했다.

VLAN은 2계층 브로드캐스트 도메인을 하드웨어 수준에서 격리하며, 서로 다른 VLAN 간의 트래픽은 반드시 3계층 라우팅 장비를 경유해야 한다. 따라서 라우터에 접근 제어 목록(ACL)이나 방화벽 정책을 적용하면 부서 간 횡적 통신을 정밀하게 통제할 수 있다.

## 5. 검증 및 회고

### 5.1. 다계층 네트워크 격리 및 통신 경로 검증

작성한 파이썬 스크립트와 시뮬레이터 구성을 구동하여 네트워크 격리 및 경로 판정의 결정론적 정확성을 검증했다.

`check_ip.py`는 공인 IP와 사설 IP를 오탐 없이 정확히 분리했으며, `subnetting.py`는 지정된 조직 규모에 맞추어 유효 호스트 범위를 오버랩 없이 정밀하게 분할했다.

| 검증 대상 스크립트 | 주요 입력 데이터 | 실행 결과 및 출력 값 | 판정 |
|---|---|---|---|
| `check_ip.py` | `10.0.0.8`, `172.20.5.6`, `172.32.5.6` | `[사설]`, `[사설]`, `[공인]` 정상 판별 | 통과 |
| `subnet_mask.py` | `192.168.10.70/26` | 네트워크: `.64`, 브로드캐스트: `.127`, 가용: 62대 | 통과 |
| `subnetting.py` | 개발팀(`/26`), 운영팀(`/27`), 보안팀(`/28`) | 각각 62대, 30대, 14대 주소 블록 배정 | 통과 |
| `route.py` | PC0 -> PC1 (동일 VLAN), PC0 -> PC2 (이종 VLAN) | `스위치 직접 전달`, `게이트웨이 전달`, `통신 불가` | 통과 |

Cisco Packet Tracer 환경에서의 검증 결과 또한 이론적 설계와 완벽하게 일치했다. 라우터가 배제된 환경에서는 동일 VLAN 내부 통신만 성립하고 이종 VLAN 통신은 패킷 폐기 처리되었다. 라우터 인터페이스에 기본 게이트웨이를 활성화한 이후 비로소 Inter-VLAN 라우팅이 정상 작동함을 확인했다.

### 5.2. 현실적 회고 및 교훈

당일 실습은 이론으로 학습한 2계층 세그먼트 격리와 3계층 라우팅의 상호작용을 시뮬레이터 상에서 시각적으로 확인하는 데 집중했다.

단순히 파이썬 문법으로 알고리즘을 구현하는 데 그치지 않고, 네트워크 장비의 실제 CLI 환경에서 VLAN 태그와 라우팅 테이블이 맞물려 동작하는 현상을 직접 체감했다.

특히 서브넷 마스크를 통한 L3 논리 분할만으로는 동일 물리 세그먼트 내부의 도청 공격을 원천 차단할 수 없다는 점을 규명했다. 실무 제로 트러스트 아키텍처에서 왜 1개 서브넷마다 1개의 독립 VLAN을 일대일로 매핑하여 브로드캐스트 도메인을 완전히 격리해야 하는지 명확한 엔지니어링 근거를 도출할 수 있었다.

시간 제약 속에서도 초기 IP 설계 단계에서 예약 블록을 체계적으로 안배하는 하이브리드 서브네팅의 중요성을 배웠으며, 향후 방화벽 ACL 정책과 연계할 수 있는 견고한 네트워크 기반을 확보했다.
