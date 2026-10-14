import json
import os
import requests
from flask import current_app, request

MONITOR_URL = os.environ['MONITOR_URL']
EVENT_TOKEN = os.environ['EVENT_TOKEN']
if len(EVENT_TOKEN) < 32 or EVENT_TOKEN.startswith('CHANGE_ME'):
    raise RuntimeError('EVENT_TOKEN에 직접 생성한 32자 이상의 값을 설정해 주세요.')


def record_request(response):
    if request.path == '/health':
        return response
    event = {
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
    }
    print(json.dumps(event, ensure_ascii=False), flush=True)
    try:
        result = requests.post(
            MONITOR_URL,
            json=event,
            headers={'X-Event-Token': EVENT_TOKEN},
            timeout=(3, 10),
        )
        result.raise_for_status()
    except requests.RequestException:
        current_app.logger.warning(
            '감시 서비스에 요청 기록을 보내지 못했습니다. '
            '감시 /health 응답과 연결 설정을 확인한 뒤 다시 시도해 주세요.'
        )
    return response
