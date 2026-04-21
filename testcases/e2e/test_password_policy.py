"""
E2E P0：新增用户首次登录重置密码 / 修改密码策略后重新登录
"""
import os

import allure

from services.auth_service import AuthService
from services.password_service import PasswordService
from services.user_service import UserService
from utils.test_log import log_resource_ids, log_step_data, log_step_result
from utils.encode_util import base64_encode
from utils.random_util import random_email

USER_EMAIL = random_email()
USER_NAME = "auto_test"
USER_STATUS = "active"
NEW_PASSWORD = "difyenterprise0417"


# 修改密码策略：大写+小写+数字（requireUppercase=True）
PASSWORD_POLICY_PAYLOAD = {
    "minLength": 10,
    "requireDigit": True,
    "requireLowercase": True,
    "requireUppercase": True,
    "requireSpecial": False,
    "forbidRepeated": False,
    "forbidSequential": False,
    "expiryEnabled": False,
    "expiryDays": 1,
}

@allure.epic("Dify Enterprise")
@allure.feature("Password Management")
class TestE2ECase7P0:

    @allure.story("First Login Reset Password")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_first_login_reset_password(self, admin_client, resource_tracker):
        """
        1. 创建系统用户（email=auto_test@dify.ai, name=auto_test, status=active），获取 response 中的 password
        2. 使用该邮箱与临时密码登录企业后台，拿到登录态 cookie
        3. 用该登录态调用 check_password_status，断言 requirePasswordChange 为 True（首次登录需重置密码）
        4. 调用 reset_password 修改密码
        5. 使用新密码登录系统成员账户，验证登录成功
        """
        password_svc = PasswordService()
        # Step 1: 创建系统用户，获取临时密码
        with allure.step("Step1: 创建系统用户，获取 response 中的 password"):
            user_svc = UserService()
            log_step_data("create user payload", email=USER_EMAIL, name=USER_NAME, status=USER_STATUS)
            create_resp = user_svc.create_user_success(
                USER_EMAIL,
                name=USER_NAME,
                status=USER_STATUS,
                client=admin_client,
            )
            temp_password = create_resp.get("password") or (create_resp.get("user") or {}).get("password")
            assert temp_password, f"创建系统用户响应中未返回 password: {create_resp}"
            user_id = create_resp.get("id") or (create_resp.get("user") or {}).get("id")
            if user_id:
                resource_tracker.add_user(user_id)
            log_resource_ids(user_id=user_id)
            log_step_result("create user result", create_resp)

        # Step 2: 使用临时密码登录企业后台，拿到登录态
        with allure.step("Step2: 登录企业后台，拿到登录态 cookie"):
            user_client, login_res = AuthService.admin_login(
                email=USER_EMAIL,
                password=base64_encode(temp_password),
            )
            assert login_res.status_code == 200, (
                f"企业后台登录失败: {login_res.status_code}, {login_res.text[:300]}"
            )
            assert user_client is not None

        # Step 3: 使用该登录态调用 check_password_status，断言首次登录需重置密码
        with allure.step("Step3: 查看密码状态，校验首次登录需重置密码"):
            status_data = password_svc.check_password_status_success(client=user_client)
            assert status_data.get("requirePasswordChange") is True, (
                f"首次登录应要求重置密码，requirePasswordChange 应为 true: {status_data}"
            )
            log_step_result("password status", status_data)

        # Step 4: 调用重置密码（使用 RESET_PASSWORD_PAYLOAD）
        with allure.step("Step4: 修改密码（reset_password）"):
            reset_payload = {
                "currentPassword": "",
                "newPassword": NEW_PASSWORD,
                "confirmPassword": NEW_PASSWORD,
            }
            log_step_data("reset password payload", **reset_payload)
            password_svc.reset_password_success(client=user_client, **reset_payload)

        # Step 5: 使用新密码登录系统成员账户，验证登录成功
        with allure.step("Step5: 使用新密码登录系统成员账户"):
            _, final_login_res = AuthService.admin_login(
                email=USER_EMAIL,
                password=base64_encode(NEW_PASSWORD),
            )
            assert final_login_res.status_code == 200, (
                f"使用新密码登录失败: {final_login_res.status_code}, {final_login_res.text[:300]}"
            )

    @allure.story("Password Policy Change And Re-login")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_update_password_policy_and_login(
        self,
        admin_client,
        restore_password_policy_after_policy_test,
    ):
        """
        1. 修改密码策略为大写+小写+数字（PasswordService.update_password_policy_success）
        2. 使用 ADMIN_EMAIL/ADMIN_PASSWORD 登录，调用 check_password_status，断言 requirePasswordChange 为 True
        3. 调用 reset_password（currentPassword=ADMIN_PASSWORD, newPassword=Wyy20010417）
        4. 使用新密码重新登录，验证成功
        """
        password_svc = PasswordService()
        with allure.step("Step1: 修改密码策略为大写+小写+数字"):
            log_step_data("update password policy payload", **PASSWORD_POLICY_PAYLOAD)
            password_svc.update_password_policy_success(
                client=admin_client,
                **PASSWORD_POLICY_PAYLOAD,
            )

        with allure.step("Step2: 登录系统成员账户，校验需重置密码"):
            email = os.getenv("PWD_EMAIL")
            password = os.getenv("PWD_PASSWORD")
            new_password = os.getenv("NEW_PASSWORD_AFTER_POLICY")
            assert email and password, "请设置环境变量 PWD_EMAIL、PWD_PASSWORD"
            member_client, login_res = AuthService.admin_login(
                email=email,
                password=base64_encode(password),
            )
            assert login_res.status_code == 200, (
                f"企业后台登录失败: {login_res.status_code}, {login_res.text[:300]}"
            )
            status_data = password_svc.check_password_status_success(client=member_client)
            assert status_data.get("requirePasswordChange") is True, (
                f"requirePasswordChange 应为 true: {status_data}"
            )
            log_step_result("password status after policy change", status_data)

        with allure.step("Step3: 修改密码（reset_password）"):
            reset_payload = {
                "currentPassword": password,
                "newPassword": new_password,
                "confirmPassword": new_password,
            }
            log_step_data("reset password payload", **reset_payload)
            password_svc.reset_password_success(client=member_client, **reset_payload)

        with allure.step("Step4: 使用新密码重新登录"):
            _, final_login_res = AuthService.admin_login(
                email=email,
                password=base64_encode(new_password),
            )
            assert final_login_res.status_code == 200, (
                f"使用新密码重新登录失败: {final_login_res.status_code}, {final_login_res.text[:300]}"
            )
