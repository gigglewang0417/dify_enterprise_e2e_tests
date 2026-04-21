"""
系统用户认证
E2E P0：创建系统用户 -> 系统用户登录企业后台（admin_login）
"""
from importlib.resources import read_text

import allure
import json
from services.auth_service import AuthService
from services.user_service import UserService
from utils.test_log import log_resource_ids, log_step_data, log_step_result
from utils.encode_util import base64_encode
from utils.random_util import random_email, random_email_with_uuid, random_name
from api.auth_api import AuthAPI
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
        1. 创建系统用户，从 response 获取 password、user_id
        2. 查询系统用户（email 存在）
        3. 查询系统用户（email 不存在）
        4. 修改用户状态为 banned，并校验列表中 status
        5. 修改用户名称，并校验
        6. 修改用户邮箱，并校验
        7. 系统用户登录企业后台 admin_login（使用最终邮箱与初始 password）
        8. 重置用户密码 POST .../users/{user_id}/reset-password，校验用新密码重新登录成功
        """
        user_svc = UserService()
        auth_api = AuthAPI()

        # Step 1: 创建系统用户，获取 response 中的 password
        with allure.step("Step1: 创建系统用户"):
            log_step_data("create user payload", email=USER_EMAIL, name=USER_NAME, status=USER_STATUS)
            create_resp = user_svc.create_user_success(
                USER_EMAIL, name=USER_NAME, status=USER_STATUS, client=admin_client
            )
            user_password = create_resp.get("password") or (create_resp.get("user") or {}).get("password")
            assert user_password, f"创建系统用户响应中未返回 password: {create_resp}"
            user_id = create_resp.get("id") or (create_resp.get("user") or {}).get("id")
            assert user_id, f"创建系统用户响应中未返回 id: {create_resp}"
            resource_tracker.add_user(user_id)
            log_resource_ids(user_id=user_id)
            log_step_result("create user result", create_resp)

        with allure.step("Step2: 查询系统用户（email 存在）"):
            log_step_data(
                "list users (email exists)",
                email=USER_EMAIL,
                status="active",
                page_number=1,
                results_per_page=10,
                reverse=True,
            )
            list_exist = user_svc.list_users_success(
                client=admin_client,
                email=USER_EMAIL,
                status="active",
                page_number=1,
                results_per_page=10,
                reverse=True,
            )
            assert (list_exist.get("pagination") or {}).get("totalCount", 0) >= 1
            rows = list_exist.get("data") or []
            hit = next(
                (r for r in rows if (r.get("account") or {}).get("email") == USER_EMAIL),
                None,
            )
            assert hit is not None, f"列表中应包含已创建用户邮箱: {list_exist}"
            assert hit.get("status") == "active", f"新建用户状态应为 active: {hit}"
            log_step_result("list users (email exists)", list_exist)

        with allure.step("Step3: 查询系统用户(email 不存在)"):
            ghost_email = random_email_with_uuid(prefix="no_such_user")
            log_step_data(
                "list users (email not exists)",
                email=ghost_email,
                status="active",
                page_number=1,
                results_per_page=10,
                reverse=True,
            )
            list_empty = user_svc.list_users_success(
                client=admin_client,
                email=ghost_email,
                status="active",
                page_number=1,
                results_per_page=10,
                reverse=True,
            )
            assert (list_empty.get("pagination") or {}).get("totalCount", 0) == 0
            assert (list_empty.get("data") or []) == [], f"应无匹配用户: {list_empty}"
            log_step_result("list users (email not exists)", list_empty)

        with allure.step("Step4: 修改用户状态为 banned "):
            log_step_data(
                "update user status banned",
                user_id=user_id,
                name="test",
                email=USER_EMAIL,
                status="banned",
            )
            upd_banned = user_svc.update_user_success(
                user_id,
                client=admin_client,
                id=user_id,
                name="test",
                email=USER_EMAIL,
                status="banned",
            )
            log_step_result("update user banned", upd_banned)

            log_step_data(
                "verify list user status banned",
                email=USER_EMAIL,
                status="banned",
            )
            list_banned = user_svc.list_users_success(
                client=admin_client,
                email=USER_EMAIL,
                status="banned",
                page_number=1,
                results_per_page=10,
                reverse=True,
            )
            rows_b = list_banned.get("data") or []
            hit_b = next(
                (r for r in rows_b if (r.get("account") or {}).get("email") == USER_EMAIL),
                None,
            )
            assert hit_b is not None, f"应用 banned 后应能按 email+status=banned 查到: {list_banned}"
            assert hit_b.get("status") == "banned", f"用户状态应为 banned: {hit_b}"
            log_step_result("verify user status banned", list_banned)
            login_res = auth_api.admin_login(USER_EMAIL, base64_encode(user_password))
            assert login_res.status_code == 401, (
                f"系统用户 admin 登录成功: {login_res.status_code}, {login_res.text[:300]}"
            )
            data = json.loads(login_res.text)
            assert data.get('reason') == "USER_BANNED", (f"{data.get('reason')}")
            log_step_result("admin login result",  login_res.text)

        with allure.step("Step5: 修改用户名称 "):
            new_name = random_name()
            log_step_data(
                "update user name",
                user_id=user_id,
                name=new_name,
                email=USER_EMAIL,
                status="active",
            )
            upd_name = user_svc.update_user_success(
                user_id,
                client=admin_client,
                id=user_id,
                name=new_name,
                email=USER_EMAIL,
                status="active",
            )
            log_step_result("update user name", upd_name)

            log_step_data("verify user name", email=USER_EMAIL, status="banned")
            list_name = user_svc.list_users_success(
                client=admin_client,
                email=USER_EMAIL,
                status="active",
                page_number=1,
                results_per_page=10,
                reverse=True,
            )
            rows_n = list_name.get("data") or []
            hit_n = next(
                (r for r in rows_n if (r.get("account") or {}).get("email") == USER_EMAIL),
                None,
            )
            assert hit_n is not None, f"应能查到用户: {list_name}"
            acc_name = (hit_n.get("account") or {}).get("name")
            assert acc_name == new_name, f"名称应已更新为 {new_name}: {hit_n}"
            log_step_result("verify user name", list_name)

        with allure.step("Step6: 修改用户邮箱 "):
            new_email = random_email()
            log_step_data(
                "update user email",
                user_id=user_id,
                name=new_name,
                email=new_email,
                status="active",
            )
            upd_email = user_svc.update_user_success(
                user_id,
                client=admin_client,
                id=user_id,
                name=new_name,
                email=new_email,
                status="active",
            )
            log_step_result("update user email", upd_email)

            log_step_data("verify user email", email=new_email, status="banned")
            list_mail = user_svc.list_users_success(
                client=admin_client,
                email=new_email,
                status="active",
                page_number=1,
                results_per_page=10,
                reverse=True,
            )
            rows_m = list_mail.get("data") or []
            hit_m = next(
                (r for r in rows_m if (r.get("account") or {}).get("email") == new_email),
                None,
            )
            assert hit_m is not None, f"应能按新邮箱查到用户: {list_mail}"
            assert (hit_m.get("account") or {}).get("email") == new_email
            log_step_result("verify user email", list_mail)

        # Step 7: 系统用户登录企业后台（使用最终邮箱）
        with allure.step("Step7: 系统用户登录企业后台"):
            client, login_res = AuthService.admin_login(
                email=new_email,
                password=base64_encode(user_password),
            )
            assert login_res.status_code == 200, (
                f"系统用户 admin 登录失败: {login_res.status_code}, {login_res.text[:300]}"
            )
            assert client is not None
            log_step_result("admin login result", login_res.json() if login_res.text else {})

        with allure.step("Step8: 重置用户密码"):
            log_step_data("reset user password", user_id=user_id)
            reset_body = user_svc.reset_user_password_success(
                user_id,
                client=admin_client,
                id=user_id,
            )
            new_password = reset_body.get("password")
            assert new_password, f"重置密码响应中未返回 password: {reset_body}"
            log_step_result("reset user password", reset_body)

            log_step_data("admin login after password reset", email=new_email)
            client_after_reset, login_res_reset = AuthService.admin_login(
                email=new_email,
                password=base64_encode(new_password),
            )
            assert login_res_reset.status_code == 200, (
                f"重置密码后 admin 登录失败: {login_res_reset.status_code}, {login_res_reset.text[:300]}"
            )
            assert client_after_reset is not None
            log_step_result(
                "admin login after password reset",
                login_res_reset.json() if login_res_reset.text else {},
            )

