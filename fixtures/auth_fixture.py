"""
登录态 fixture：admin 后台登录 client、Console 登录 client。
使用 scope="session" 时整轮测试只登录一次，需登录态的用例直接注入对应 fixture 即可。
"""
import pytest
from services.auth_service import AuthService


@pytest.fixture(scope="session")
def admin_client():
    """Admin 后台已登录的 Client（BASE_URL + Cookie + X-CSRF-Token），用于 dashboard API。"""
    client, _ = AuthService.admin_login()
    return client


@pytest.fixture(scope="session")
def console_client():
    """Console 已登录的 Client（CONSOLE_URL + Cookie + refresh_token），用于 console API。"""
    client, _ = AuthService.console_login()
    return client

