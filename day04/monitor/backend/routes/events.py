from flask import Blueprint, request
from auth_helpers import api_access_error
from event_rules import make_event
from repositories import events as event_repository

events_bp = Blueprint("events", __name__)


@events_bp.get("/health")
def health():
    return {"service": "monitor", "status": "ok"}


@events_bp.post("/api/events")
def receive_event():
    event = make_event(request.get_json(silent=True))
    if event is None:
        return {"error": "method, path, status_code를 올바르게 보내 주세요."}, 400
    event_repository.create_event(event)
    return {"message": "기록을 받았습니다."}, 201


@events_bp.get("/api/events")
def get_events():
    error = api_access_error()
    if error:
        return error
    event_type = request.args.get("event_type")
    allowed = {"login_success", "login_failure", "http_request"}
    if event_type is not None and event_type not in allowed:
        return {"error": "지원하지 않는 이벤트 종류입니다."}, 400
    return {"events": event_repository.list_events(event_type)}
