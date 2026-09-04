# 4교시. 스위치와 라우터 — 같은 망 안과 밖의 전달

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

checks = [("PC0", "PC1", False), ("PC0", "PC2", True), ("PC0", "PC2", False)]
for source, destination, router_exists in checks:
    print(source, "->", destination, decide_path(source, destination, router_exists))