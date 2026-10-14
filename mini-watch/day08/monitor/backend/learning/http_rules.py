from datetime import datetime


def parse_time(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def select_views(events):
    views = []
    for event in events:
        if (
            event.get("method") == "GET"
            and event.get("path") == "/"
            and event.get("status_code") == 200
            and event.get("kind") == "post_list"
        ):
            views.append(event)
    return views


def count_views(views):
    return len(views)


def find_following_errors(events, views, max_seconds=30):
    if not views:
        return []
    last_view_time = parse_time(views[-1]["occurred_at"])
    errors = []
    for event in events:
        if event.get("status_code") == 404:
            err_time = parse_time(event["occurred_at"])
            gap = (err_time - last_view_time).total_seconds()
            if 0 < gap <= max_seconds:
                errors.append(event)
    return errors


def evaluate_threshold(count, threshold=10):
    return count >= threshold
