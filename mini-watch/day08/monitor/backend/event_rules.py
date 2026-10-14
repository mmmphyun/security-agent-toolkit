EVENT_TYPES = {
    "login_success", "login_failure", "logout_request", "http_request",
    "post_list", "post_view", "post_create_request",
    "post_update_request", "post_delete_request", "request_error",
}


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

    parts = path.strip("/").split("/")
    post_detail = len(parts) == 2 and parts[0] in {"board", "posts"} and parts[1].isdecimal()
    post_action = len(parts) == 3 and parts[0] == "board" and parts[1].isdecimal()
    login_path = path in {"/auth/login", "/api/auth/login"}

    if method == "POST" and login_path and status == 200:
        event_type = "login_success"
    elif method == "POST" and login_path and status == 401:
        event_type = "login_failure"
    elif method == "POST" and path in {"/logout", "/api/auth/logout"}:
        event_type = "logout_request"
    elif method == "POST" and path == "/board/new":
        event_type = "post_create_request"
    elif method == "POST" and post_action and parts[2] == "edit":
        event_type = "post_update_request"
    elif method == "POST" and post_action and parts[2] == "delete":
        event_type = "post_delete_request"
    elif status >= 400:
        event_type = "request_error"
    elif method == "GET" and path == "/" and status == 200:
        event_type = "post_list"
    elif method == "GET" and post_detail and status == 200:
        event_type = "post_view"
    else:
        event_type = "http_request"

    return {"method": method, "path": path, "status_code": status, "event_type": event_type}
