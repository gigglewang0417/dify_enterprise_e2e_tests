import os
import allure
from api.console_api import invite_workspace_members_by_email
from services.auth_service import AuthService
from services.member_service import MemberService, _extract_member_id_from_detail
from services.worksapce_service import WorkspaceService
from utils.test_log import log_resource_ids, log_step_data, log_step_result
from utils.encode_util import base64_encode
from utils.random_util import random_email, random_name

WORKSPACE_NAME = random_name()
WORKSPACE_EMAIL = os.getenv("ADMIN_EMAIL")
WORKSPACE_INVALID_EMAIL = random_email()

@allure.epic("Dify Enterprise")
@allure.feature("Workspace Management")
class TestCreateWorkspace:

    @allure.story("Create Workspace Success")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_workspace_success(self, admin_client, resource_tracker):
        """创建 workspace 成功（成员存在)。"""
        """删除工作区成功"""
        workspace_svc = WorkspaceService()
        # 1. 创建工作空间
        log_step_data("create workspace payload", name=WORKSPACE_NAME, status="normal", email=WORKSPACE_EMAIL)
        workspace = workspace_svc.create_workspace_success(
            name=WORKSPACE_NAME,
            status="normal",
            email=WORKSPACE_EMAIL,
            client=admin_client,
        )
        workspace_id = workspace.get("id")
        log_resource_ids(workspace_id=workspace_id)
        log_step_result("create workspace result", workspace)

        # 2. 删除工作空间
        workspace_svc.delete_workspace_success(workspace_id, admin_client)

    @allure.story("Create Workspace Failure")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_workspace_failure(self, admin_client):
        """创建 workspace 失败（无效邮箱/成员不存在）：返回 404 MEMBER_NOT_FOUND。"""
        workspace_svc = WorkspaceService()
        log_step_data("create workspace invalid payload", name=WORKSPACE_NAME, status="normal", email=WORKSPACE_INVALID_EMAIL)
        res = workspace_svc.create_workspace_response(
            name=WORKSPACE_NAME,
            status="normal",
            email=WORKSPACE_INVALID_EMAIL,
            client=admin_client,
        )
        assert res.status_code == 404, f"预期 404: {res.status_code}, {res.text[:300]}"
        data = res.json()
        assert data.get("reason") == "MEMBER_NOT_FOUND", data

    @allure.story("Update Workspace Attributes")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_workspace_success(self, admin_client, resource_tracker, created_member):
        """修改工作空间成功：创建成员 → 修改 Name 与 Owner Email → 查询校验名称已更新。"""
        workspace_svc = WorkspaceService()
        # 1. 创建成员（由 created_member fixture 提供，用例结束后自动删除）
        owner_email = created_member["email"]

        # 2. 先创建一个工作空间
        res = workspace_svc.create_workspace_success(
            name=WORKSPACE_NAME,
            status="normal",
            email=owner_email,
            client=admin_client,
        )
        workspace_id = res.get("id")
        log_resource_ids(workspace_id=workspace_id, owner_email=owner_email)
        try:
            # 3. 在编辑页修改：Name
            new_name = random_name()
            workspace_svc.update_workspace_success(
                workspace_id,
                client=admin_client,
                name=new_name,
                email=owner_email,
                status="normal",
            )

            # 4. 修改成功后查询当前工作空间，校验名称已修改成功
            workspace = workspace_svc.get_workspace_success(workspace_id, admin_client)
            assert workspace.get("name") == new_name, f"工作空间名称未更新为 {new_name}"
            log_step_result("workspace after name update", workspace)

            # 5. 在编辑页修改：status
            workspace_svc.update_workspace_success(
                workspace_id,
                client=admin_client,
                name=new_name,
                email=owner_email,
                status="archive",
            )
            # 6. 修改成功后查询当前工作空间，校验状态已修改成功
            workspace = workspace_svc.get_workspace_success(workspace_id, admin_client)
            assert workspace.get("status") == "archive", f"工作空间名称未更新为archive "
            log_step_result("workspace after status update", workspace)

            # 7. 在编辑页修改：email
            new_owner_email = created_member["email"]
            workspace_svc.update_workspace_success(
                workspace_id,
                client=admin_client,
                name=new_name,
                email=new_owner_email,
                status="normal",
            )
            # 8. 修改成功后查询当前工作空间，校验email已修改成功
            workspace = workspace_svc.get_workspace_success(workspace_id, admin_client)
            owner = workspace.get("owner")
            assert owner.get("email") == new_owner_email, f"Owner Email 未更新为 {new_owner_email}"
            log_step_result("workspace after owner update", workspace)

            # 9. 在编辑页修改：无效的邮箱
            invaild_owner_email = random_email()
            update_res = workspace_svc.update_workspace_response(
                workspace_id,
                client=admin_client,
                name=new_name,
                email=invaild_owner_email,
                status="archive",
            )
            assert update_res.status_code == 404, f"修改 workspace 失败: {update_res.status_code}, {update_res.text[:300]}"
        finally:
            # 先清理 workspace，用例返回后 created_member fixture 再清理 member
            if workspace_id:
                try:
                    WorkspaceService().delete_workspace_success(workspace_id, admin_client)
                except Exception:
                    pass

    @allure.story("Archive Workspace Then Block Console Login")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_adjust_workspace_status_and_console_login(self, admin_client, created_member_workspace):
        """调整工作空间状态：created_member_workspace 创建成员与工作空间 → 使用该成员 Console 登录（登录此工作空间）。"""
        workspace_svc = WorkspaceService()
        # 1. 调用 created_member_workspace 创建成员、工作空间
        member_info, workspace_id = created_member_workspace
        assert member_info.get("email"), "member_info 应有 email"
        assert member_info.get("password") is not None, "member_info 应有 password（创建成员接口返回）"
        assert workspace_id, "应有 workspace_id"
        log_resource_ids(workspace_id=workspace_id, member_id=member_info.get("id"))

        # 2. 登录此工作空间：使用该成员账号调用 Console 登录
        client, res = AuthService.console_login(
            email=member_info["email"],
            password=member_info["password"],
        )
        assert client is not None, "Console 登录应返回 client"
        assert res.status_code == 200, f"Console 登录预期 200: {res.status_code}, {res.text[:300]}"

        # 3. 修改工作空间状态normal为archive
        workspace_svc.update_workspace_success(
            workspace_id,
            client=admin_client,
            name=WORKSPACE_NAME,
            email=member_info["email"],
            status="archive",
        )

        # 4.登录此工作空间：预期登录失败
        res = AuthService.console_login_response(
            email=member_info["email"],
            password=base64_encode(member_info["password"]),
        )
        login_res = res.json()
        assert login_res.get("result") == "fail", f"Console 登录失败, {login_res}"
        log_step_result("archive workspace login result", login_res)

    @allure.story("Join Member To Workspace")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_join_workspace_member_success(self, admin_client, resource_tracker, created_member):
        """工作空间中加入成员：created_member 创建成员 → POST /workspaces/{id}/member 加入 → list_members(workspace_id) 校验存在且 role 符合预期。"""
        workspace_svc = WorkspaceService()
        member_svc = MemberService()
        # 1. 使用 fixture created_member 创建成员
        member_id = created_member["id"]
        member_email = created_member["email"]
        expected_role = "normal"

        # 2. 先创建一个工作空间（owner 用 ADMIN_EMAIL）
        res = workspace_svc.create_workspace_success(
            name=WORKSPACE_NAME,
            status="normal",
            email=WORKSPACE_EMAIL,
            client=admin_client,
        )
        workspace_id = res.get("id")
        resource_tracker.add_workspace(workspace_id=workspace_id)
        log_resource_ids(workspace_id=workspace_id, member_id=member_id)

        # 3. 将创建的成员加入工作空间：POST /v1/dashboard/api/workspaces/{workspace_id}/member
        join_payload = {
            "email": member_email,
            "id": member_id,
            "role": expected_role,
        }
        workspace_svc.join_workspace_success(workspace_id, client=admin_client, **join_payload)
        log_step_result("join workspace payload", join_payload)

        # 4. 加入成功后查询当前工作空间成员：list_members(workspace_id=workspace_id)，校验存在此成员且 role 符合预期
        list_data = member_svc.list_members_success(client=admin_client, workspace_id=workspace_id)
        # 接口返回为数组 [{ account: { id, email }, workspaces: [{ role, workspaceId }, ...] }, ...]
        members = list_data.get("data")
        found = next(
            (m for m in members if (m.get("account") or {}).get("id") == member_id or (m.get("account") or {}).get("email") == member_email),
            None,
        )
        assert found is not None, f"工作空间中未找到成员 id={member_id} email={member_email}, 列表: {members}"
        # 在该成员的 workspaces 中查找当前 workspace_id 对应的 role
        ws_entry = next((w for w in (found.get("workspaces") or []) if w.get("workspaceId") == workspace_id), None)
        assert ws_entry is not None, f"成员未加入工作空间 {workspace_id}, workspaces: {found.get('workspaces')}"
        assert ws_entry.get("role") == expected_role, f"成员在该工作空间中 role 不符合预期: expected {expected_role}, got {ws_entry.get('role')}"
        log_step_result("workspace member list result", list_data)

        # 4. 重复添加成员
        join_payload = {
            "email": member_email,
            "id": member_id,
            "role": expected_role,
        }
        join_res = workspace_svc.join_workspace_response(workspace_id, client=admin_client, **join_payload)
        assert join_res.status_code == 400, f"重复添加成员预期 400: {join_res.status_code}, {join_res.text[:300]}"
        err_data = join_res.json()
        assert err_data.get("reason") == "MEMBER_ALREADY_EXISTS", err_data

        # 5. 添加不存在的成员
        invalid_email = random_email()
        invaild_id = "f01230a7-gh8b-4p48-c478-9f53d00db520"
        join_payload = {
            "email": invalid_email,
            "id": invaild_id,
            "role": expected_role,
        }
        join_res = workspace_svc.join_workspace_response(workspace_id, client=admin_client, **join_payload)
        assert join_res.status_code == 404, f"添加不存在的成员符合预期 404: {join_res.status_code}, {join_res.text[:300]}"
        err_data = join_res.json()
        assert err_data.get("reason") == "MEMBER_NOT_FOUND", err_data

    @allure.story("Invite Member Permission")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_invite_member_permission(self, admin_client, resource_tracker, created_member_workspace):
        """
        前置：created_member_workspace 创建 owner 与工作空间。
        Step1：再创建成员，以 admin 加入该工作空间，并用该成员 Console 登录得到登录态。
        Step2：创建成员并以 Step1 的 Console 登录态邀请该成员，校验邀请结果后登录该成员。
        Step3：企业后台关闭工作空间「成员邀请」开关（allowMemberInvite=false）。
        Step4：再创建成员，用 Step1 的 Console 登录态调用邀请接口；校验该成员 Console 登录成功。
        """
        member_svc = MemberService()
        workspace_svc = WorkspaceService()
        owner_info, workspace_id = created_member_workspace
        assert workspace_id, "created_member_workspace 应返回 workspace_id"
        log_resource_ids(workspace_id=workspace_id, owner_member_id=owner_info.get("id"))

        # Step1：创建成员 → 加入工作空间 admin → Console 登录态
        with allure.step("Step1: 创建成员并以 admin 加入工作空间，获取 Console 登录态"):
            admin_member_email = random_email(prefix="invite_admin")
            admin_member_name = random_name()
            log_step_data(
                "create member for workspace admin",
                email=admin_member_email,
                name=admin_member_name,
            )
            create_data = member_svc.create_member_success(
                email=admin_member_email,
                name=admin_member_name,
                client=admin_client,
            )
            admin_member_id = create_data.get("id") or (create_data.get("member") or {}).get("id")
            admin_password = create_data.get("password") or (create_data.get("member") or {}).get("password") or ""
            assert admin_member_id, f"创建成员未返回 id: {create_data}"
            assert admin_password, f"创建成员未返回 password: {create_data}"
            resource_tracker.add_member(admin_member_id)
            log_resource_ids(invite_admin_member_id=admin_member_id)

            join_payload = {
                "email": admin_member_email,
                "id": admin_member_id,
                "role": "admin",
            }
            log_step_data("join workspace as admin", workspace_id=workspace_id, **join_payload)
            workspace_svc.join_workspace_success(
                workspace_id,
                client=admin_client,
                **join_payload,
            )
            log_step_result("join workspace as admin", join_payload)

            log_step_data("console login as workspace admin", email=admin_member_email)
            console_client, console_res = AuthService.console_login(
                email=admin_member_email,
                password=admin_password,
            )
            assert console_client is not None, "Console 登录应返回 client"
            assert console_res.status_code == 200, (
                f"Console 登录失败: {console_res.status_code}, {console_res.text[:300]}"
            )
            log_step_result(
                "console login as workspace admin",
                console_res.json() if console_res.text else {},
            )

        # Step2：当前工作空间上下文下邀请成员（邮箱为 Step1 成员）
        with allure.step("Step2: 邀请成员"):
            normal_member_email = random_email(prefix="invite_admin")
            normal_member_name = random_name()
            log_step_data(
                "create member for workspace admin",
                email=normal_member_email,
                name=normal_member_name,
            )
            create_data = member_svc.create_member_success(
                email=normal_member_email,
                name=normal_member_name,
                client=admin_client,
            )
            normal_member_id = create_data.get("id") or (create_data.get("member") or {}).get("id")
            normal_password = create_data.get("password") or (create_data.get("member") or {}).get("password") or ""
            assert normal_member_id, f"创建成员未返回 id: {create_data}"
            assert normal_password, f"创建成员未返回 password: {create_data}"
            resource_tracker.add_member(normal_member_id)
            log_resource_ids(invite_admin_member_id=normal_member_id)
            log_step_data(
                "invite_workspace_members_by_email",
                emails=[normal_member_email],
                role="normal",
                language="zh-Hans",
            )
            inv_res = invite_workspace_members_by_email(
                console_client,
                emails=[normal_member_email],
                role="normal",
                language="zh-Hans",
            )
            assert inv_res.status_code in (200, 201), (
                f"邀请成员失败: {inv_res.status_code}, {inv_res.text[:500]}"
            )
            body = inv_res.json() if inv_res.text else {}
            assert body.get("result") == "success", f"result 应为 success: {body}"
            invitation_results = body.get("invitation_results") or []
            assert isinstance(invitation_results, list) and len(invitation_results) >= 1, (
                f"invitation_results 应非空: {body}"
            )
            first = invitation_results[0]
            assert first.get("status") == "success", f"邀请条目 status 应为 success: {first}"
            assert first.get("email") == normal_member_email, f"邀请邮箱应一致: {first}"
            log_step_result("invite workspace members by email", body)

            console_client, console_res = AuthService.console_login(
                email=normal_member_email,
                password=normal_password,
            )
            assert console_client is not None, "Console 登录应返回 client"
            assert console_res.status_code == 200, (
                f"Console 登录失败: {console_res.status_code}, {console_res.text[:300]}"
            )
            log_step_result(
                "console login as workspace normal",
                console_res.json() if console_res.text else {},
            )

        with allure.step("Step3: 关闭成员邀请开关"):
            log_step_data(
                "update_workspace_permission",
                workspace_id=workspace_id,
                allowMemberInvite=False,
                allowOwnerTransfer=True,
            )
            perm_data = workspace_svc.update_workspace_permission_success(
                workspace_id,
                client=admin_client,
                permission_body={
                    "allowMemberInvite": False,
                    "allowOwnerTransfer": True,
                },
            )
            log_step_result("update_workspace_permission (invite off)", perm_data)

        # with allure.step("Step4: 创建成员、邀请并校验该成员 Console 登录"):
        #     invitee_email = random_email(prefix="invite_member")
        #     invitee_name = random_name()
        #     log_step_data("create member for invite", email=invitee_email, name=invitee_name)
        #     invitee_create = member_svc.create_member_success(
        #         email=invitee_email,
        #         name=invitee_name,
        #         client=admin_client,
        #     )
        #     invitee_member_id = invitee_create.get("id")
        #     invitee_password = invitee_create.get("password")
        #     assert invitee_member_id, f"创建成员未返回 id: {invitee_create}"
        #     assert invitee_password, f"创建成员未返回 password: {invitee_create}"
        #     resource_tracker.add_member(invitee_member_id)
        #     log_resource_ids(step4_invitee_member_id=invitee_member_id)
        #
        #     log_step_data(
        #         "invite_workspace_members_by_email (step1 console session)",
        #         emails=[invitee_email],
        #         role="normal",
        #         language="zh-Hans",
        #     )
        #     inv_res = invite_workspace_members_by_email(
        #         console_client,
        #         emails=[invitee_email],
        #         role="normal",
        #         language="zh-Hans",
        #     )
        #     if inv_res.status_code in (200, 201):
        #         body = inv_res.json() if inv_res.text else {}
        #         assert body.get("result") == "success", f"result 应为 success: {body}"
        #         inv_list = body.get("invitation_results") or []
        #         assert isinstance(inv_list, list) and len(inv_list) >= 1, (
        #             f"invitation_results 应非空: {body}"
        #         )
        #         first = inv_list[0]
        #         assert first.get("status") == "success", f"邀请条目 status 应为 success: {first}"
        #         assert first.get("email") == invitee_email, f"邀请邮箱应一致: {first}"
        #         assert body.get("tenant_id"), f"响应应含 tenant_id: {body}"
        #         log_step_result("invite workspace members ", body)
        #     else:
        #         log_step_result(
        #             "invite workspace members step4 (non-2xx, 关闭邀请后接口可能拒绝)",
        #             {"status_code": inv_res_s4.status_code, "text": (inv_res_s4.text or "")[:500]},
        #         )
        #
        #     log_step_data("console login as  member", email=invitee_email)
        #     invitee_client, invitee_login_res = AuthService.console_login(
        #         email=invitee_email,
        #         password=invitee_password,
        #     )
        #     assert invitee_client is not None, "被邀请/新建成员 Console 登录应返回 client"
        #     assert invitee_login_res.status_code == 200, (
        #         f"Step4 成员 Console 登录失败: {invitee_login_res.status_code}, {invitee_login_res.text[:300]}"
        #     )
        #     log_step_result(
        #         "console login as  member",
        #         invitee_login_res.json() if invitee_login_res.text else {},
        #     )


@allure.epic("Dify Enterprise")
@allure.feature("Workspace Management")
class TestDefaultWorkspace:
    @allure.story("Default Workspace Operations")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_default_workspace_operations(
        self,
        admin_client,
        resource_tracker,
        ensure_no_default_workspace,
        created_member_workspace,
    ):
        """
        前置：ensure_no_default_workspace 确保当前无默认工作空间；created_member_workspace 创建 owner 与工作空间。

        Step1：将前置创建的工作空间设为当前用户默认工作空间。
        Step2：查询默认工作空间，确认为 Step1 所设。
        Step3：新建成员、加入该工作空间，查询成员详情，确认工作空间列表包含该默认工作空间。
        Step4：使用该成员账号 Console 登录成功。
        """
        workspace_svc = WorkspaceService()
        member_svc = MemberService()
        owner_info, workspace_id = created_member_workspace
        assert workspace_id, "created_member_workspace 应返回 workspace_id"
        log_resource_ids(workspace_id=workspace_id, owner_member_id=owner_info.get("id"))

        with allure.step("Step1: 添加默认工作空间"):
            log_step_data("set_default_workspace", workspace_id=workspace_id)
            set_data = workspace_svc.set_default_workspace_success(
                workspace_id,
                client=admin_client,
            )
            log_step_result("set_default_workspace", set_data)

        with allure.step("Step2: 查询默认工作空间"):
            default_data = workspace_svc.get_default_workspace_success(client=admin_client)
            assert (default_data.get("workspaceId") == workspace_id) or (
                str(default_data.get("workspaceId")) == str(workspace_id)
            ), f"默认 workspaceId 应与 Step1 一致: {default_data}"
            ws = default_data.get("workspace") or {}
            assert (ws.get("id") == workspace_id) or (str(ws.get("id")) == str(workspace_id)), (
                f"默认 workspace.id 应与 Step1 一致: {default_data}"
            )
            log_step_result("get_default_workspace", default_data)

        with allure.step("Step3: 成员加入工作空间，查询成员详情并校验工作空间列表"):
            member_email = random_email(prefix="default_ws")
            member_name = random_name()
            log_step_data("create member for default workspace list", email=member_email, name=member_name)
            create_data = member_svc.create_member_success(
                email=member_email,
                name=member_name,
                client=admin_client,
            )
            member_id = _extract_member_id_from_detail(create_data)
            member_password = create_data.get("password") or (create_data.get("member") or {}).get("password") or ""
            assert member_id, f"创建成员未返回 id: {create_data}"
            assert member_password, f"创建成员未返回 password: {create_data}"
            resource_tracker.add_member(member_id)
            log_resource_ids(step3_member_id=member_id)

            detail = member_svc.list_members_success(email=member_email, client=admin_client)
            rows = detail.get("data")
            matched = next(
                (
                    r
                    for r in rows
                    if str((r.get("account") or {}).get("id")) == str(member_id)
                    or (r.get("account") or {}).get("email") == member_email
                ),
                None,
            )
            row = matched or rows[0]
            workspaces = row.get("workspaces") or []
            found = next(
                (
                    w
                    for w in workspaces
                    if w.get("workspaceId") == workspace_id
                    or str(w.get("workspaceId")) == str(workspace_id)
                    or w.get("id") == workspace_id
                    or str(w.get("id")) == str(workspace_id)
                ),
                None,
            )
            assert found is not None, (
                f"成员工作空间列表应包含默认工作空间 {workspace_id}, workspaces={workspaces}, detail={detail}"
            )
            log_step_result("get_member workspaces contains default workspace", {"found": found, "detail": detail})

        with allure.step("Step4: 登录成员 Console 成功"):
            log_step_data("console login as step3 member", email=member_email)
            console_client, console_res = AuthService.console_login(
                email=member_email,
                password=member_password,
            )
            assert console_client is not None, "Console 登录应返回 client"
            assert console_res.status_code == 200, (
                f"Console 登录失败: {console_res.status_code}, {console_res.text[:300]}"
            )
            log_step_result(
                "console login success",
                console_res.json() if console_res.text else {},
            )