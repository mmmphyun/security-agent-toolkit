from learning.normalize import normalize_events
from learning.http_rules import select_views, count_views, find_following_errors, evaluate_threshold


def build_report(events, threshold=10):
    normalized = normalize_events(events)
    views = select_views(normalized)
    following_errors = find_following_errors(normalized, views)

    count = count_views(views)
    triggered = evaluate_threshold(count, threshold)

    records = views + following_errors
    evidence = [r["id"] for r in records]

    status = "검토 후보" if triggered else "기준 미해당"
    reason = "일반 서비스의 목록 조회 횟수다. 사용자/IP별 판정이나 공격 확정은 아니다."
    basis = f"새 관찰 이후·첫 결과 기준 최근 60초·GET /·200·post_list / 기준 {threshold}회 이상"

    card = {
        "rule": "HTTP 조회 규칙",
        "source": "실제 HTTP",
        "observed": count,
        "threshold": threshold,
        "basis": basis,
        "triggered": triggered,
        "status": status,
        "evidence": evidence,
        "records": records,
        "reason": reason,
    }

    return {
        "ready": True,
        "card": card,
        "results": [card],
    }
