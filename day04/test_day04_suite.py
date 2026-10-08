import urllib.request
import urllib.parse
import json
import http.cookiejar
import sys

BASE_GENERAL = "http://127.0.0.1:5100"
BASE_MONITOR = "http://127.0.0.1:5173"  # Vite Proxy 경유

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def log(step, msg, ok=True):
    mark = "[PASS]" if ok else "[FAIL]"
    print(f"{mark} [{step}] {msg}")

def request_json(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = opener.open(req)
        raw = resp.read().decode("utf-8")
        return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed

def run_tests():
    print("=== Mini Watch Day 4 종합 기능 및 체크리스트 검증 ===")
    
    # 1. 일반 서비스 게시글 및 404 요청 발생
    try:
        req1 = urllib.request.Request(f"{BASE_GENERAL}/")
        with urllib.request.urlopen(req1) as r:
            assert r.status == 200
        log("1-1", "일반 서비스 메인 페이지 요청 성공 (200)")
    except Exception as e:
        log("1-1", f"일반 서비스 메인 요청 실패: {e}", False)

    try:
        req2 = urllib.request.Request(f"{BASE_GENERAL}/board/99999")
        urllib.request.urlopen(req2)
    except urllib.error.HTTPError as e:
        assert e.code == 404
        log("1-2", "존재하지 않는 게시글 주소 접속 시 404 발생 확인")
    except Exception as e:
        log("1-2", f"404 요청 예외: {e}", False)

    # 2. 감시 대시보드 CSRF 토큰 발급 확인 (/api/auth/me)
    status, data = request_json(f"{BASE_MONITOR}/api/auth/me")
    assert status == 200 and "csrf_token" in data
    csrf_token = data["csrf_token"]
    log("2-1", f"초기 세션 수립 및 CSRF 토큰 확보 성공: {csrf_token[:10]}...")

    # 3. 로그인 실패 케이스 (400 빈 입력, 401 불일치)
    headers = {"X-CSRF-Token": csrf_token}
    status, data = request_json(f"{BASE_MONITOR}/api/auth/login", "POST", {"username": "", "password": ""}, headers)
    assert status == 400
    log("3-1", f"빈 입력값 로그인 시 400 거절 확인: {data.get('error')}")

    status, data = request_json(f"{BASE_MONITOR}/api/auth/login", "POST", {"username": "operator", "password": "wrong_password"}, headers)
    assert status == 401
    log("3-2", f"비밀번호 불일치 로그인 시 401 거절 확인: {data.get('error')}")

    # 4. 올바른 계정 로그인 (operator / Learn123!)
    status, data = request_json(f"{BASE_MONITOR}/api/auth/login", "POST", {"username": "operator", "password": "Learn123!"}, headers)
    assert status == 200 and data.get("user", {}).get("username") == "operator"
    csrf_token = data["csrf_token"]
    headers["X-CSRF-Token"] = csrf_token
    log("4-1", "올바른 계정 로그인 성공 (200) 및 사용자 정보 수신")

    # 5. 요청 기록(GET /api/events) 확인 (200 및 404 로그 수집 검증)
    status, data = request_json(f"{BASE_MONITOR}/api/events")
    assert status == 200 and "events" in data
    events = data["events"]
    assert len(events) > 0
    paths = [ev["path"] for ev in events]
    status_codes = [ev["status_code"] for ev in events]
    assert any("99999" in p for p in paths)
    assert 404 in status_codes
    log("5-1", f"수집된 요청 기록 확인 완료 (총 {len(events)}건, 404 이벤트 포함)")

    # 6. 관찰 메모 작성 (POST /api/notes)
    note_payload = {
        "title": "없는 게시글 404 요청 확인",
        "body": "board/99999 경로에 접속하여 404 Not Found가 발생한 내역을 모니터링함."
    }
    status, data = request_json(f"{BASE_MONITOR}/api/notes", "POST", note_payload, headers)
    assert status == 201 and "note" in data
    created_note = data["note"]
    note_id = created_note["id"]
    log("6-1", f"새 관찰 메모 작성 성공 (ID: {note_id}, 제목: {created_note['title']})")

    # 7. 관찰 메모 목록 및 상세 조회
    status, data = request_json(f"{BASE_MONITOR}/api/notes")
    assert status == 200 and "notes" in data
    assert any(n["id"] == note_id for n in data["notes"])
    log("7-1", f"관찰 메모 목록에 등록된 메모({note_id}) 존재 확인")

    status, data = request_json(f"{BASE_MONITOR}/api/notes/{note_id}")
    assert status == 200 and data["note"]["title"] == note_payload["title"]
    log("7-2", f"관찰 메모 상세 조회 성공 (내용 일치 확인)")

    # 8. 관찰 메모 빈 값/공백 수정 시도 (400 거절 및 기존 내용 보존)
    status, data = request_json(f"{BASE_MONITOR}/api/notes/{note_id}", "PUT", {"title": "   ", "body": "   "}, headers)
    assert status == 400
    log("8-1", f"공백 내용 수정 시도에 대해 400 거절 확인: {data.get('error')}")

    status, data = request_json(f"{BASE_MONITOR}/api/notes/{note_id}")
    assert data["note"]["title"] == note_payload["title"]
    log("8-2", "400 거절 후 기존 메모 내용 보존 확인")

    # 9. 관찰 메모 정상 수정 (PUT /api/notes/<id>)
    update_payload = {
        "title": "없는 게시글 404 요청 확인 (조치 완료)",
        "body": "해당 비정상 접근에 대한 검토를 마쳤으며 보안 로그에 기록함."
    }
    status, data = request_json(f"{BASE_MONITOR}/api/notes/{note_id}", "PUT", update_payload, headers)
    assert status == 200 and data["note"]["title"] == update_payload["title"]
    log("9-1", "관찰 메모 정상 수정 성공 (200)")

    # 10. 존재하지 않는 메모 요청 404 검증
    status, data = request_json(f"{BASE_MONITOR}/api/notes/999999")
    assert status == 404
    status, data = request_json(f"{BASE_MONITOR}/api/notes/999999", "PUT", update_payload, headers)
    assert status == 404
    status, data = request_json(f"{BASE_MONITOR}/api/notes/999999", "DELETE", None, headers)
    assert status == 404
    log("10-1", "존재하지 않는 메모 ID 조회/수정/삭제 시 404 반환 확인")

    # 11. 관찰 메모 삭제 (DELETE /api/notes/<id>)
    status, data = request_json(f"{BASE_MONITOR}/api/notes/{note_id}", "DELETE", None, headers)
    assert status == 200
    log("11-1", f"메모({note_id}) 삭제 성공 (200)")

    status, data = request_json(f"{BASE_MONITOR}/api/notes/{note_id}")
    assert status == 404
    log("11-2", f"삭제된 메모 재조회 시 404 반환 확인")

    # 12. 로그아웃 (POST /api/auth/logout)
    status, data = request_json(f"{BASE_MONITOR}/api/auth/logout", "POST", None, headers)
    assert status == 200 and data["user"] is None
    log("12-1", "로그아웃 성공 및 사용자 상태 비움 확인")

    # 13. 로그아웃 후 보호 API 접근 거절 (401)
    status, data = request_json(f"{BASE_MONITOR}/api/events")
    assert status == 401
    status, data = request_json(f"{BASE_MONITOR}/api/notes")
    assert status == 401
    log("13-1", "로그아웃 후 보호 대상 API(events, notes) 접근 시 401 거절 확인")

    print("\n[SUCCESS] 모든 20개 필수 검증 항목 및 인증 보안 검증 통과!")

if __name__ == "__main__":
    run_tests()
