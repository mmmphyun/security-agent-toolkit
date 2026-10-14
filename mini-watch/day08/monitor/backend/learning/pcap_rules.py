from pathlib import Path
from scapy.all import rdpcap

DATA = Path(__file__).parent / "data"


def read_capture(name):
    return rdpcap(str(DATA / name))


def capture_summary(name, seconds=5):
    packets = read_capture(name)
    start = min(float(packet.time) for packet in packets)
    selected = [packet for packet in packets if start <= float(packet.time) < start + seconds]
    return {
        "name": name,
        "seconds": seconds,
        "packets": len(selected),
        "bytes": sum(len(bytes(packet)) for packet in selected),
    }


def traffic_exceeded(normal, observed, multiple=2):
    return observed["bytes"] > normal["bytes"] * multiple


def main():
    print("=== [심화 미션 1] PCAP 독립 실습 (교육용 합성 패킷 분석) ===")
    print("주의: 이 자료는 직접 생성한 교육용 패킷이며, 실제 게시판 요청 로그와 분리된 독립 실습입니다.\n")

    for sec in [5, 1]:
        normal = capture_summary("normal.pcap", seconds=sec)
        observed = capture_summary("observed.pcap", seconds=sec)
        exceeded = traffic_exceeded(normal, observed, multiple=2)
        print(f"[구간: 첫 패킷부터 {sec}초]")
        print(f"  - 정상 (normal.pcap): {normal['packets']}개 패킷, {normal['bytes']} bytes")
        print(f"  - 관찰 (observed.pcap): {observed['packets']}개 패킷, {observed['bytes']} bytes")
        print(f"  - 2배 초과 판정: {exceeded}")
        print(
            f"  - 해석: {sec}초 관찰 구간 설정에 따라 포착되는 패킷 수와 바이트 합이 달라집니다.\n"
        )


if __name__ == "__main__":
    main()
