import os
from urllib.parse import urlparse

import requests

from common.observability import log_http_interaction


class Client:

    def __init__(self):
        self.base_url = (os.getenv("BASE_URL") or "").rstrip("/")
        self.session = requests.Session()

    def _build_url(self, path):
        """拼接请求 URL：path 为绝对路径（如 /v1/dashboard/api/...），避免 base_url 与 path 重复 /v1。"""
        if not path or not isinstance(path, str):
            path = ""
        path = path.strip()
        if path.startswith("http"):
            return path
        # 若 path 被拼入 None（如 "None/v1/dashboard/..."），去掉前导 "None" 并保证以 / 开头
        if path.startswith("None/"):
            path = "/" + path[5:]
        elif path == "None":
            path = ""
        base = self.base_url.rstrip("/")
        # base_url 已含 /v1 且 path 以 /v1 开头时，去掉 path 前多余的 /v1，避免得到 .../v1/v1/...
        if base.endswith("/v1") and path.startswith("/v1/"):
            path = path[4:]  # "/v1/dashboard/..." -> "/dashboard/..."
        elif base.endswith("/v1") and path == "/v1":
            path = ""
        return base + path if (path.startswith("/") or not path) else base + "/" + path

    def _cookie_domain(self):
        """与浏览器一致：Cookie 的 domain 为 BASE_URL 的 host（如 enterprise-platform.dify.dev）。"""
        parsed = urlparse(self.base_url)
        return parsed.hostname or ""

    def set_login_cookies(self, access_token, csrf_token, locale="zh-Hans", refresh_token=None):
        """将登录得到的 token 设为 Cookie，供后续请求携带（与浏览器请求头一致）。
        与浏览器 Cookie 对齐：__Host-access_token、__Host-csrf_token、locale；
        可选 refresh_token（Console 登录会带 __Host-refresh_token）。
        """
        domain = self._cookie_domain()
        path = "/"
        self.session.cookies.set("__Host-access_token", access_token, path=path, domain=domain)
        self.session.cookies.set("__Host-csrf_token", csrf_token, path=path, domain=domain)
        self.session.cookies.set("locale", locale, path=path, domain=domain)
        if refresh_token:
            self.session.cookies.set("__Host-refresh_token", refresh_token, path=path, domain=domain)
        self.session.headers.setdefault("Content-Type", "application/json")
        # Dify 企业版要求请求头带 X-CSRF-Token，与 Cookie 中 __Host-csrf_token 一致，否则返回 401
        self.session.headers["X-CSRF-Token"] = csrf_token

    def _prepare_request(self, method, url, **kwargs):
        """发请求前确保 CSRF 头与 Cookie 一致（Cookie 可能被更新）。"""
        csrf = self.session.cookies.get("__Host-csrf_token")
        if csrf:
            self.session.headers["X-CSRF-Token"] = csrf

    def _send(self, method, path, **kwargs):
        url = self._build_url(path)
        self._prepare_request(method, url, **kwargs)
        response = self.session.request(method=method, url=url, **kwargs)
        log_http_interaction(
            method=method,
            url=url,
            kwargs={
                "params": kwargs.get("params"),
                "json": kwargs.get("json"),
                "data": kwargs.get("data"),
                "headers": dict(self.session.headers),
            },
            response=response,
            source="client",
        )
        return response

    def get(self, path, **kwargs):
        return self._send("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._send("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self._send("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._send("DELETE", path, **kwargs)
