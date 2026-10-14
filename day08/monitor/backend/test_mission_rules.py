from datetime import datetime, timezone, timedelta
from event_rules import make_event
from learning.normalize import normalize_event, normalize_events
from learning.http_rules import select_views, count_views, find_following_errors
from learning.report import build_report


def test_event_rules():
    assert make_event({"method": "GET", "path": "/", "status_code": 200})["event_type"] == "post_list"
    assert make_event({"method": "GET", "path": "/training-missing", "status_code": 404})["event_type"] == "request_error"
    assert make_event({"method": "POST", "path": "/auth/login", "status_code": 200})["event_type"] == "login_success"
    assert make_event({"method": "POST", "path": "/auth/login", "status_code": 401})["event_type"] == "login_failure"


def test_normalization():
    raw = {
        "id": 42,
        "method": "GET",
        "path": "/",
        "status_code": 200,
        "event_type": "post_list",
        "occurred_at": "2026-10-14T07:00:00+00:00",
    }
    norm = normalize_event(raw)
    assert raw["id"] == 42  # 원본 불변
    assert norm["id"] == "http-42"
    assert norm["source"] == "http_live"
    assert norm["kind"] == "post_list"
    assert "actor" not in norm or norm.get("actor") is None
    assert "ip" not in norm or norm.get("ip") is None


def test_http_selection_and_errors():
    t0 = datetime(2026, 10, 14, 7, 0, 0, tzinfo=timezone.utc)
    raw_events = []
    # 12회 목록 조회 (1초 간격)
    for i in range(1, 13):
        raw_events.append({
            "id": i,
            "method": "GET",
            "path": "/",
            "status_code": 200,
            "event_type": "post_list",
            "occurred_at": (t0 + timedelta(seconds=i)).isoformat(),
        })
    # 마지막 조회 뒤 5초 후 발생한 404 (30초 이내)
    raw_events.append({
        "id": 13,
        "method": "GET",
        "path": "/training-missing",
        "status_code": 404,
        "event_type": "request_error",
        "occurred_at": (t0 + timedelta(seconds=17)).isoformat(),
    })
    # 35초 후 발생한 404 (30초 초과이므로 제외되어야 함)
    raw_events.append({
        "id": 14,
        "method": "GET",
        "path": "/too-late",
        "status_code": 404,
        "event_type": "request_error",
        "occurred_at": (t0 + timedelta(seconds=50)).isoformat(),
    })

    normalized = normalize_events(raw_events)
    views = select_views(normalized)
    assert len(views) == 12
    assert count_views(views) == 12

    errors = find_following_errors(normalized, views, max_seconds=30)
    assert len(errors) == 1
    assert errors[0]["id"] == "http-13"

    # 조회가 없을 때 404 오류도 비워지는지 검증
    no_views_errors = find_following_errors(normalized, [], max_seconds=30)
    assert no_views_errors == []


def test_build_report():
    t0 = datetime(2026, 10, 14, 7, 0, 0, tzinfo=timezone.utc)
    raw_events = []
    for i in range(1, 13):
        raw_events.append({
            "id": i, "method": "GET", "path": "/", "status_code": 200,
            "event_type": "post_list",
            "occurred_at": (t0 + timedelta(seconds=i)).isoformat(),
        })
    raw_events.append({
        "id": 13, "method": "GET", "path": "/training-missing", "status_code": 404,
        "event_type": "request_error",
        "occurred_at": (t0 + timedelta(seconds=15)).isoformat(),
    })

    # 기준 10
    rep10 = build_report(raw_events, threshold=10)
    card10 = rep10["card"]
    assert card10["observed"] == 12
    assert card10["threshold"] == 10
    assert card10["triggered"] is True
    assert card10["status"] == "검토 후보"
    assert len(card10["records"]) == 13
    assert len(card10["evidence"]) == 13

    # 기준 20 (같은 데이터)
    rep20 = build_report(raw_events, threshold=20)
    card20 = rep20["card"]
    assert card20["observed"] == 12
    assert card20["threshold"] == 20
    assert card20["triggered"] is False
    assert card20["status"] == "기준 미해당"
    assert len(card20["records"]) == 13
    assert len(card20["evidence"]) == 13


def test_empty_observation():
    rep = build_report([], threshold=10)
    card = rep["card"]
    assert card["observed"] == 0
    assert card["triggered"] is False
    assert card["status"] == "기준 미해당"
    assert len(card["records"]) == 0
    assert len(card["evidence"]) == 0


if __name__ == "__main__":
    test_event_rules()
    test_normalization()
    test_http_selection_and_errors()
    test_build_report()
    test_empty_observation()
    print("ALL TESTS PASSED!")
