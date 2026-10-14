from datetime import datetime, timezone
from flask import Blueprint, request
from auth_helpers import api_access_error
from learning.support import last_event_id, live_events
from learning.report import build_report

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.get("/api/analysis/start")
def observation_start():
    error = api_access_error()
    if error:
        return error
    return {"after_id": last_event_id(), "seconds": 60}


@analysis_bp.get("/api/analysis")
def analysis():
    error = api_access_error()
    if error:
        return error
    try:
        threshold = int(request.args.get("threshold", "10"))
        after_id = int(request.args.get("after_id", "-1"))
    except ValueError:
        return {"error": "기준과 시작ID는 정수여야 합니다."}, 400
    if not 1 <= threshold <= 100 or after_id < 0:
        return {"error": "새 관찰을 시작하고 기준1~100을 입력해 주세요."}, 400
    reference_at = None
    reference_text = request.args.get("reference_time")
    if reference_text:
        try:
            reference_at = datetime.fromisoformat(reference_text)
            if reference_at.tzinfo is None or reference_at > datetime.now(timezone.utc):
                raise ValueError("invalid reference time")
        except ValueError:
            return {"error": "관찰 기준시각이 올바르지 않습니다. 새 관찰을 시작해 주세요."}, 400
    events, at = live_events(after_id, reference_at=reference_at)
    report = build_report(events, threshold)
    report.update({
        "after_id": after_id,
        "window_seconds": 60,
        "reference_time": at,
        "time_basis": "monitor_received_at",
    })
    return report
