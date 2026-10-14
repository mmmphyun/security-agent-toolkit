from pathlib import Path
from learning.support import read_json
from learning.normalize import normalize_events
from learning.http_rules import select_views, count_views, find_following_errors


def main():
    data_path = Path(__file__).parent / "data" / "observation.json"
    if not data_path.exists():
        print(f"오류: {data_path} 파일이 없습니다. capture_case를 먼저 실행해 주세요.")
        return

    raw_events = read_json("observation.json")
    normalized = normalize_events(raw_events)
    views = select_views(normalized)
    errors = find_following_errors(normalized, views, max_seconds=30)
    count = count_views(views)

    print(f"1. 목록 조회 횟수(관찰값): {count}회")
    print(f"2. 마지막 조회 뒤 30초 이내 뒤따른 404 오류 수: {len(errors)}건")
    if errors:
        for err in errors:
            print(f"   뒤따른 404 - ID: {err['id']}, 경로: {err['path']}, 수신시각: {err['occurred_at']}")
    print(f"3. 최종 근거 행 총합 (조회 {count}행 + 뒤따른 오류 {len(errors)}행): {count + len(errors)}행")
    print("4. 주의: 뒤따른 404는 근거 행에만 포함되며 조회 횟수(관찰값)에는 더해지지 않습니다.")


if __name__ == "__main__":
    main()
