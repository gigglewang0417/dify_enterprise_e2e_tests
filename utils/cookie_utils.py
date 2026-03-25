"""从 HTTP 响应中解析 Set-Cookie，提取登录态 token。"""


def parse_tokens_from_set_cookie(res):
    """从 Set-Cookie 响应头解析 __Host-access_token 与 __Host-csrf_token。

    当 res.cookies 未解析到时回退使用（如多值 Set-Cookie 时）。
    支持多个 Set-Cookie 头（服务端通常每个 cookie 一条头，按逗号拆分会误伤 value 内的逗号）。

    Returns:
        (access_token, csrf_token)，未解析到时为 (None, None)。
    """
    access_token = None
    csrf_token = None
    set_cookie_lines = []
    if hasattr(res, "raw") and res.raw is not None and hasattr(res.raw, "msg") and res.raw.msg is not None:
        get_all = getattr(res.raw.msg, "get_all", None)
        if callable(get_all):
            set_cookie_lines = get_all("Set-Cookie") or []
    if not set_cookie_lines:
        raw = res.headers.get("Set-Cookie") or res.headers.get("set-cookie") or ""
        set_cookie_lines = [s.strip() for s in raw.split(",") if s.strip()]
    for line in set_cookie_lines:
        line = line.strip()
        if line.startswith("__Host-access_token="):
            access_token = line.split(";", 1)[0].split("=", 1)[1].strip()
        elif line.startswith("__Host-csrf_token="):
            csrf_token = line.split(";", 1)[0].split("=", 1)[1].strip()
    return access_token, csrf_token


def _get_set_cookie_lines(res):
    """从 response 中取出所有 Set-Cookie 行（列表）。"""
    set_cookie_lines = []
    if hasattr(res, "raw") and res.raw is not None and hasattr(res.raw, "msg") and res.raw.msg is not None:
        get_all = getattr(res.raw.msg, "get_all", None)
        if callable(get_all):
            set_cookie_lines = get_all("Set-Cookie") or []
    if not set_cookie_lines:
        raw = res.headers.get("Set-Cookie") or res.headers.get("set-cookie") or ""
        set_cookie_lines = [s.strip() for s in raw.split(",") if s.strip()]
    return set_cookie_lines


def parse_console_tokens_from_set_cookie(res):
    """从 Console 登录响应的 Set-Cookie 中解析 __Host-access_token、__Host-refresh_token、__Host-csrf_token。

    Returns:
        (access_token, refresh_token, csrf_token)，未解析到时为 (None, None, None)。
    """
    access_token = None
    refresh_token = None
    csrf_token = None
    for line in _get_set_cookie_lines(res):
        line = line.strip()
        if line.startswith("__Host-access_token="):
            access_token = line.split(";", 1)[0].split("=", 1)[1].strip()
        elif line.startswith("__Host-refresh_token="):
            refresh_token = line.split(";", 1)[0].split("=", 1)[1].strip()
        elif line.startswith("__Host-csrf_token="):
            csrf_token = line.split(";", 1)[0].split("=", 1)[1].strip()
    return access_token, refresh_token, csrf_token
