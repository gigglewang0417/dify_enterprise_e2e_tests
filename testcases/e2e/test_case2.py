"""
系统用户认证
E2E P0：创建系统用户 -> 系统用户登录企业后台（admin_login）
"""
import allure

from services.auth_service import AuthService
from services.user_service import UserService
from utils.test_log import log_resource_ids, log_step_data, log_step_result
from utils.encode_util import base64_encode
from utils.random_util import random_email
# 步骤 1：创建系统用户
USER_EMAIL = random_email()
USER_NAME = "auto_test"
USER_STATUS = "active"


@allure.epic("Dify Enterprise")
@allure.feature("User Management")
class TestE2ECase2P0:

    @allure.story("System User Admin Login")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_system_user_create_and_admin_login(self, admin_client, resource_tracker):
        """
        1. 创建系统用户（email=auto_test@dify.ai, name=auto_test, status=active），创建成功从 response 获取 password
        2. 系统用户登录企业后台，调用 admin_login 使用该 email 与 password
        """
        # Step 1: 创建系统用户，获取 response 中的 password
        with allure.step("Step1: 创建系统用户"):
            log_step_data("create user payload", email=USER_EMAIL, name=USER_NAME, status=USER_STATUS)
            user_svc = UserService()
            create_resp = user_svc.create_user_success(
                USER_EMAIL, name=USER_NAME, status=USER_STATUS, client=admin_client
            )
            user_password = create_resp.get("password") or (create_resp.get("user") or {}).get("password")
            assert user_password, f"创建系统用户响应中未返回 password: {create_resp}"
            user_id = create_resp.get("id")
            resource_tracker.add_user(user_id)
            log_resource_ids(user_id=user_id)
            log_step_result("create user result", create_resp)

        # Step 2: 系统用户登录企业后台（调用 admin_login）
        with allure.step("Step2: 系统用户登录企业后台"):
            client, login_res = AuthService.admin_login(
                email=USER_EMAIL,
                password=base64_encode(user_password),
            )
            assert login_res.status_code == 200, (
                f"系统用户 admin 登录失败: {login_res.status_code}, {login_res.text[:300]}"
            )
            assert client is not None
            log_step_result("admin login result", login_res.json() if login_res.text else {})
