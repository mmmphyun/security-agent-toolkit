from pathlib import Path
from learning.support import read_json
from learning.normalize import normalize_events
from learning.http_rules import select_views, count_views, evaluate_threshold


def main():
    data_path = Path(__file__).parent / "data" / "observation.json"
    if not data_path.exists():
        print(f"오류: {data_path} 파일이 없습니다. capture_case를 먼저 실행해 주세요.")
        return

    raw_events = read_json("observation.json")
    normalized = normalize_events(raw_events)
    views = select_views(normalized)
    count = count_views(views)

    print(f"관찰값(조회 횟수): {count}회")

    for th in [10, 20]:
        triggered = evaluate_threshold(count, th)
        status = "검토 후보" if triggered else "기준 미해당"
        print(f"기준 {th} 비교 (count >= {th}): {triggered} ({status})")


if __name__ == "__main__":
    main()
