"""
工作空间认证
E2E P0：创建新成员 -> 为新成员创建工作空间 -> 新成员 Console 登录
"""

import allure

from services.auth_service import AuthService
from services.member_service import MemberService
from services.worksapce_service import WorkspaceService
from utils.test_log import log_resource_ids, log_step_data, log_step_result
from utils.encode_util import base64_encode
from utils.random_util import random_email, random_name
MEMBER_NAME = random_name()
MEMBER_EMAIL = random_email()
WORKSPACE_NAME = random_name()
WORKSPACE_STATUS = "normal"


@allure.epic("Dify Enterprise")
@allure.feature("Workspace Management")
class TestE2ECase1P0:

    @allure.story("Member Workspace Console Login")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_new_member_workspace_and_console_login(self, admin_client, resource_tracker):
        """
        1. 创建新成员（随机邮箱），创建成功从 response 获取 password
        2. 为新成员创建新工作空间（name/email 固定），status=normal
        3. 使用新成员 email 与步骤 1 获得的密码进行 Console 登录
        """

        # 1: 创建新成员，获取 response 中的 password
        member_svc = MemberService()
        workspace_svc = WorkspaceService()
        with allure.step("Step1: 创建新成员（随机邮箱）"):
            log_step_data("create member payload", email=MEMBER_EMAIL, name=MEMBER_NAME, status="active")
            create_resp = member_svc.create_member_success(
                MEMBER_EMAIL, name=MEMBER_NAME, client=admin_client
            )
            member_id = create_resp["id"]
            member_password = create_resp.get("password") or (create_resp.get("member") or {}).get("password")
            assert member_password, f"创建成员响应中未返回 password: {create_resp}"
            resource_tracker.add_member(member_id)
            log_resource_ids(member_id=member_id)
            log_step_result("create member result", create_resp)

        # 2.添加新成员（邮箱已存在）
        with allure.step("Step2: 创建新成员（邮箱已存在）"):
            res = member_svc.create_member_response(
                MEMBER_EMAIL,
                name=MEMBER_NAME,
                status="active",
                client=admin_client,
            )
            assert res.status_code == 409, f"创建成员成功: {res.status_code}, {res.text[:300]}"
            data = res.json()
            assert data.get("reason") == "MEMBER_ALREADY_EXISTS", data

        # 3: 为新成员创建新工作空间（使用 admin 登录后创建）
        with allure.step("Step3: 为新成员创建新工作空间"):
            log_step_data("create workspace payload", name=WORKSPACE_NAME, status=WORKSPACE_STATUS, email=MEMBER_EMAIL)
            create_resp = workspace_svc.create_workspace_success(
                WORKSPACE_NAME,
                WORKSPACE_STATUS,
                MEMBER_EMAIL,
                client=admin_client,
            )
            workspace_id = create_resp["id"]
            resource_tracker.add_workspace(workspace_id)
            log_resource_ids(workspace_id=workspace_id)
            log_step_result("create workspace result", create_resp)

        # 4: 新成员使用 email 与步骤 1 的 password 登录 Console
        with allure.step("Step4: 登录新工作空间"):
            console_client, login_res = AuthService.console_login(
                email=MEMBER_EMAIL,
                password=member_password,
            )
            assert login_res.status_code == 200, f"Console 登录失败: {login_res.status_code}, {login_res.text[:300]}"
            login_data = login_res.json() if login_res.text else {}
            assert login_data.get("result") == "success", f"Console 登录 result 非 success: {login_data}"
            log_step_result("console login result", login_data)

        # 5: 修改成员name
        with allure.step("Step5: 修改成员name"):
            new_name = random_name()
            payload = {"id": member_id, "name": new_name, "email": MEMBER_EMAIL, "status": "active"}
            member_svc.update_member_success(member_id, client=admin_client, **payload)
            member_info = member_svc.list_members_success(client=admin_client, email=MEMBER_EMAIL)
            members = member_info.get("data")
            found = next(
                (m for m in members if (m.get("account") or {}).get(
                    "name") == new_name),
                None,
            )
            assert found is not None, f"工作空间中未找到成员 id={member_id} name={new_name}, 列表: {members}"

        # 6: 修改成员email
        with allure.step("Step6: 修改成员email"):
            new_email = random_email()
            payload = {"id": member_id, "name": new_name, "email": new_email, "status": "active"}
            member_svc.update_member_success(member_id, client=admin_client, **payload)
            member_info = member_svc.list_members_success(client=admin_client, email=new_email)
            members = member_info.get("data")
            found = next(
                (m for m in members if (m.get("account") or {}).get(
                    "id") == member_id),
                None,
            )
            assert found is not None, f"工作空间中未找到成员 id={member_id} email={new_email}, 列表: {members}"

        # 7. 重置成员密码
        with allure.step("Step7: 重置成员密码"):
            payload = {"id": member_id}
            data = member_svc.reset_member_password_success(member_id, client=admin_client, **payload)
            new_password = data.get("password")
            log_step_result("reset member password result", data)
            console_client, login_res = AuthService.console_login(
                email=new_email,
                password=new_password,
            )
            assert login_res.status_code == 200, f"Console 登录失败: {login_res.status_code}, {login_res.text[:300]}"

        # 8.禁用成员
        with allure.step("Step8: 禁用成员"):
            payload = {"id": member_id, "name": new_name, "email": new_email, "status": "banned"}
            member_svc.update_member_success(member_id, client=admin_client, **payload)
            res = AuthService.console_login_response(
                email=new_email,
                password=base64_encode(new_password))
            login_res = res.json()
            assert login_res.get("code") == "account_banned", f"Console 登录成功, {login_res}"
            log_step_result("banned account login result", login_res)
