import os

import allure

from services.auth_service import AuthService
from utils.test_log import log_resource_ids, log_step_data, log_step_result


@allure.epic("Dify Enterprise")
@allure.feature("Authentication")
class TestLogin:

    @allure.story("Admin Login")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_admin_login_success(self):
        # 使用登录请求返回的状态码 200 判断用例是否成功
        log_step_data("admin login account", email=os.getenv("ADMIN_EMAIL"))
        client, login_res = AuthService.admin_login()
        assert login_res.status_code == 200
        log_resource_ids(admin_login_status=login_res.status_code)
        log_step_result("admin login response", login_res.json() if login_res.text else {})

    @allure.story("Console Login")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_console_login_success(self):
        log_step_data("console login account", email=os.getenv("CONSOLE_EMAIL") or os.getenv("ADMIN_EMAIL"))
        client, login_res = AuthService.console_login()
        assert login_res.status_code == 200
        log_resource_ids(console_login_status=login_res.status_code)
        log_step_result("console login response", login_res.json() if login_res.text else {})

    @allure.story("Console SAML SSO Login")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_console_saml_sso_login_success(self):
        """Console SAML SSO：生成 SAML -> POST ACS -> 用返回 session 调 /console/api/me 验证登录。"""
        email = os.getenv("SAML_SSO_EMAIL") or os.getenv("CONSOLE_EMAIL")
        if not email:
            raise RuntimeError("请设置环境变量 SAML_SSO_EMAIL 或 CONSOLE_EMAIL 以运行 SAML SSO 用例")
        log_step_data("saml login account", email=email)
        client, acs_res = AuthService.saml_login(email, console_url=os.getenv("CONSOLE_URL"))
        assert acs_res.status_code == 200
        # ACS 通常返回 200 或 302，只要未 4xx/5xx 即视为已建 session
        assert acs_res.status_code in (200, 302), f"ACS 响应异常: {acs_res.status_code} {acs_res.text[:200]}"
        log_resource_ids(saml_login_status=acs_res.status_code)
        log_step_result("saml acs response", acs_res.text[:500] if acs_res.text else "")
