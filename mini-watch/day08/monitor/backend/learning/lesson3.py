from pathlib import Path
from learning.support import read_json
from learning.normalize import normalize_events
from learning.http_rules import select_views, count_views


def main():
    data_path = Path(__file__).parent / "data" / "observation.json"
    if not data_path.exists():
        print(f"오류: {data_path} 파일이 없습니다. capture_case를 먼저 실행해 주세요.")
        return

    raw_events = read_json("observation.json")
    normalized = normalize_events(raw_events)
    views = select_views(normalized)
    count = count_views(views)

    print(f"1. 전체 정규화 이벤트: {len(normalized)}행")
    print(f"2. 네 조건(GET, /, 200, post_list) 만족 조회 선택: {count}행")
    print(f"3. 선택된 조회 근거 ID 목록: {[v['id'] for v in views]}")

    # 404 제외 확인
    excluded_404 = [e for e in normalized if e["status_code"] == 404 and e not in views]
    print(f"4. 조회에서 제외된 404 이벤트 수: {len(excluded_404)}행")


if __name__ == "__main__":
    main()
