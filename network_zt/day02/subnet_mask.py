#2교시. 서브넷 마스크와 CIDR — 주소의 경계선

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

result = summarize_subnet("192.168.10.70/26")
if result:
    print("네트워크:", result["network"])
    print("브로드캐스트:", result["broadcast"])
    print("호스트 범위:", result["first_host"], "~", result["last_host"])
    print("사용 가능:", result["usable"])
