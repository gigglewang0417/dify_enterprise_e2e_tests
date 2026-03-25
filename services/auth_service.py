import os

from common.client import Client
from utils.cookie_utils import (
    parse_console_tokens_from_set_cookie,
    parse_tokens_from_set_cookie,
)
from utils.encode_util import base64_encode
from utils.sso_generator import post_saml_acs


class AuthService:

    @staticmethod
    def _require_env(name):
        value = os.getenv(name)
        if value in (None, ""):
            raise RuntimeError(f"缺少环境变量 {name}")
        return value

    @classmethod
    def _build_admin_login_payload(cls, email=None, password=None):
        return {
            "email": email or cls._require_env("ADMIN_EMAIL"),
            "password": password if password is not None else base64_encode(cls._require_env("ADMIN_PASSWORD")),
        }

    @classmethod
    def _build_console_login_payload(cls, email=None, password=None):
        console_email = email or os.getenv("CONSOLE_EMAIL") or os.getenv("ADMIN_EMAIL")
        raw_password = password if password is not None else (os.getenv("CONSOLE_PASSWORD") or os.getenv("ADMIN_PASSWORD"))
        if not console_email:
            raise RuntimeError("缺少 Console 登录邮箱，请设置 CONSOLE_EMAIL 或 ADMIN_EMAIL")
        if not raw_password:
            raise RuntimeError("缺少 Console 登录密码，请设置 CONSOLE_PASSWORD 或 ADMIN_PASSWORD")
        return {
            "email": console_email,
            "password": base64_encode(raw_password),
            "language": "zh-Hans",
            "remember_me": True,
        }

    @staticmethod
    def admin_login_response(email, password):
        client = Client()
        payload = {"email": email, "password": password}
        return client.post("/dashboard/api/login", json=payload)

    @staticmethod
    def console_login_response(email, password, language="zh-Hans", remember_me=True):
        client = Client()
        client.base_url = AuthService._require_env("CONSOLE_URL").rstrip("/")
        payload = {
            "email": email,
            "password": password,
            "language": language,
            "remember_me": remember_me,
        }
        return client.post("/console/api/login", json=payload)

    @staticmethod
    def admin_login(email=None, password=None):
        """Admin 企业后台登录。若传入 email、password 则使用其登录，否则使用环境变量 ADMIN_EMAIL、ADMIN_PASSWORD（会 base64 编码）。"""
        client = Client()

        payload = AuthService._build_admin_login_payload(email=email, password=password)

        res = client.post("/dashboard/api/login", json=payload)

        if res.status_code != 200:
            raise RuntimeError(
                f"Login failed: status {res.status_code}, body: {res.text[:200]}"
            )

        # 与浏览器请求头一致：从响应 Cookie/Set-Cookie 取 __Host-access_token、__Host-csrf_token
        access_token = res.cookies.get("__Host-access_token")
        csrf_token = res.cookies.get("__Host-csrf_token")

        # 若 Set-Cookie 未被 requests 解析到 res.cookies，则从响应头回退解析
        if not access_token or not csrf_token:
            access_token, csrf_token = parse_tokens_from_set_cookie(res)

        if not access_token:
            raise RuntimeError(
                "Login response 中未找到 access_token（请检查 response headers 或 Set-Cookie）"
            )
        if not csrf_token:
            raise RuntimeError(
                "Login response 中未找到 csrf_token（请检查 response headers 或 Set-Cookie）"
            )

        # 写入 session 的 Cookie，后续请求会自动带上（与浏览器一致）
        client.set_login_cookies(
            access_token=access_token,
            csrf_token=csrf_token,
            locale="zh-Hans",
        )

        return client, res

    @staticmethod
    def console_login(email=None, password=None):
        """Console 登录：使用 CONSOLE_URL，保存 access_token、refresh_token、csrf_token 到 Cookie。
        若传入 email、password 则使用其登录，否则使用环境变量 CONSOLE_EMAIL/CONSOLE_PASSWORD 或 ADMIN_EMAIL/ADMIN_PASSWORD。
        """
        client = Client()
        client.base_url = AuthService._require_env("CONSOLE_URL").rstrip("/")

        payload = AuthService._build_console_login_payload(email=email, password=password)

        res = client.post("/console/api/login", json=payload)

        if res.status_code != 200:
            raise RuntimeError(
                f"Console login failed: status {res.status_code}, body: {res.text[:200]}"
            )
        data = res.json() if res.text else {}
        if data.get("result") != "success":
            raise RuntimeError(
                f"Console login response result not success: {data}"
            )

        access_token = res.cookies.get("__Host-access_token")
        refresh_token = res.cookies.get("__Host-refresh_token")
        csrf_token = res.cookies.get("__Host-csrf_token")
        if not access_token or not csrf_token:
            access_token, refresh_token, csrf_token = parse_console_tokens_from_set_cookie(res)

        if not access_token:
            raise RuntimeError(
                "Console login 响应中未找到 access_token（请检查 Set-Cookie）"
            )
        if not csrf_token:
            raise RuntimeError(
                "Console login 响应中未找到 csrf_token（请检查 Set-Cookie）"
            )

        client.set_login_cookies(
            access_token=access_token,
            csrf_token=csrf_token,
            locale="zh-Hans",
            refresh_token=refresh_token,
        )

        return client, res

    @staticmethod
    def saml_login(email, console_url=None):
        """
        Console SAML SSO 登录：生成 SAMLResponse -> POST ACS -> 创建 session（Cookie）-> 返回带登录态的 Client。
        步骤：1 生成 SAML Assertion Base64  2 POST /console/api/enterprise/sso/saml/acs  3 使用响应 Cookie
        """
        session, res = post_saml_acs(email, console_url=console_url)

        base = (console_url or AuthService._require_env("CONSOLE_URL")).rstrip("/")
        client = Client()
        client.base_url = base
        client.session = session
        client.session.headers.setdefault("Content-Type", "application/json")
        csrf = session.cookies.get("__Host-csrf_token")
        if csrf:
            client.session.headers["X-CSRF-Token"] = csrf

        return client, res
