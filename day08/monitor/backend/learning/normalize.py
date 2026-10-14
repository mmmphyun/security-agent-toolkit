def normalize_event(raw):
    event = raw.copy()
    raw_id = raw.get("id")
    event["id"] = f"http-{raw_id}" if not str(raw_id).startswith("http-") else str(raw_id)
    event["source"] = "http_live"
    event["kind"] = raw.get("event_type") or raw.get("kind")
    # method, path, status_code, occurred_at 보존
    return event


def normalize_events(events):
    return [normalize_event(event) for event in events]
