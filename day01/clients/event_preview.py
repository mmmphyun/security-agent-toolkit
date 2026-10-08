import json
from datetime import datetime, timezone

event = {
    'occurred_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'service': 'general',
    'method': 'GET',
    'path': '/posts/999',
    'post_id': 999,
    'http_status': 404,
    'upstream_status': 404,
    'duration_ms': 12.5,
    'transport_error': None,
}
print(json.dumps(event, ensure_ascii=False))