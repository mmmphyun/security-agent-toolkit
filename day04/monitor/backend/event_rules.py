def make_event(data):
    if not isinstance(data, dict):
        return None
    method = data.get("method")
    path = data.get("path")
    status = data.get("status_code")
    allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    if not isinstance(method, str) or method not in allowed_methods:
        return None
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        return None
    if type(status) is not int or not 100 <= status <= 599:
        return None

    login_path = path in {"/auth/login", "/api/auth/login"}
    if method == "POST" and login_path and status == 200:
        event_type = "login_success"
    elif method == "POST" and login_path and status == 401:
        event_type = "login_failure"
    else:
        event_type = "http_request"
    return {"method": method, "path": path, "status_code": status, "event_type": event_type}
