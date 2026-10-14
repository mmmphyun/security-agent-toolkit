from pathlib import Path
from learning.support import read_json
from learning.normalize import normalize_events


def main():
    data_path = Path(__file__).parent / "data" / "observation.json"
    if not data_path.exists():
        print(f"오류: {data_path} 파일이 없습니다. capture_case를 먼저 실행해 주세요.")
        return

    raw_events = read_json("observation.json")
    print(f"1. 원본 이벤트 수: {len(raw_events)}행")

    normalized = normalize_events(raw_events)
    print(f"2. 정규화된 이벤트 수: {len(normalized)}행")

    for i, event in enumerate(normalized, 1):
        print(
            f"   [{i}] ID: {event['id']}, source: {event['source']}, "
            f"kind: {event['kind']}, method: {event['method']}, "
            f"path: {event['path']}, status: {event['status_code']}, "
            f"occurred_at: {event['occurred_at']}"
        )

    # 404 보존 확인
    status_404 = [e for e in normalized if e["status_code"] == 404]
    print(f"3. 정규화 후 보존된 404 이벤트 수: {len(status_404)}행")


if __name__ == "__main__":
    main()
