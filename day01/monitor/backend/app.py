import json
from datetime import datetime, timezone
from time import perf_counter
import requests
from flask import Flask

app = Flask(__name__)
app.json.ensure_ascii = False  # JSON 응답의 한글을 그대로 표시

@app.get('/posts/<int:post_id>')
def observe_post(post_id):
    occurred_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    started = perf_counter()
    reply = requests.get(f'http://127.0.0.1:5100/posts/{post_id}', timeout=1)
    body = reply.json()
    duration_ms = round((perf_counter() - started) * 1000, 1)
    event = {
        'occurred_at': occurred_at,
        'service': 'general',
        'method': 'GET',
        'path': f'/posts/{post_id}',
        'post_id': post_id,
        'http_status': reply.status_code,
        'upstream_status': reply.status_code,
        'duration_ms': duration_ms,
        'transport_error': None,
    }
    print(json.dumps(event, ensure_ascii=False), flush=True)
    return body, reply.status_code