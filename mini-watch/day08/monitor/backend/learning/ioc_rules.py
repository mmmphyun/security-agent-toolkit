import json
from pathlib import Path

DATA = Path(__file__).parent / "data"


def read_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def find_ioc_matches(events, indicators):
    matches = []
    for event in events:
        if event.get("address") in indicators or event.get("ip") in indicators:
            matches.append(event)
    return matches


def find_ioc_mismatches(events, indicators):
    mismatches = []
    for event in events:
        ip = event.get("address") or event.get("ip")
        if ip not in indicators:
            mismatches.append(event)
    return mismatches


def main():
    print("=== [심화 미션 2] IOC 일치 실습 (문서용 예제 IP 대조) ===")
    print("주의: 이 결과는 교육용 감사 자료 예제일 뿐이며, 실제 악성 IP 확정 결과가 아닙니다.")
    print("      또한 실제 HTTP 이벤트 원본(http_events)에는 클라이언트 IP 필드가 저장되지 않으므로,")
    print("      HTTP 요청 로그만으로는 실제 사용자나 출발지 IP를 식별할 수 없습니다.\n")

    indicators = read_json("indicators.json")
    audit_events = read_json("audit-raw.json")

    matches = find_ioc_matches(audit_events, indicators)
    mismatches = find_ioc_mismatches(audit_events, indicators)

    print(f"대조 대상 IOC 목록: {indicators}")
    print(f"전체 감사 이벤트 수: {len(audit_events)}건")
    print(f"IOC 일치 이벤트 수: {len(matches)}건")
    for m in matches:
        print(f"  - [일치] ID: {m.get('id')}, Person: {m.get('person')}, IP: {m.get('address')}, Action: {m.get('action')}")

    print(f"IOC 불일치 이벤트 수: {len(mismatches)}건")
    for mm in mismatches[:3]:
        print(f"  - [불일치] ID: {mm.get('id')}, Person: {mm.get('person')}, IP: {mm.get('address')}, Action: {mm.get('action')}")


if __name__ == "__main__":
    main()
