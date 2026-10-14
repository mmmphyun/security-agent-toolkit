import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


def remove_request_secrets(event, hint):
    # 로그인 비밀번호와 세션 쿠키는 오류 수집 자료에서 제외한다.
    request_data = event.get('request', {})
    for key in ('data', 'cookies', 'headers', 'query_string'):
        request_data.pop(key, None)
    event.pop('user', None)
    return event


def configure_errors(service_name):
    dsn = os.environ.get('SENTRY_DSN', '').strip()
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        environment=os.environ.get('SENTRY_ENVIRONMENT', service_name),
        release=os.environ.get('APP_VERSION', 'day2-v1'),
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size='never',
        traces_sample_rate=0.0,
        before_send=remove_request_secrets,
    )
    sentry_sdk.set_tag('service', service_name)
