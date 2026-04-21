"""
ADMIN API
E2E P0：企业后台创建 secret key -> 使用 secret key 调用 Admin API 获取工作空间列表
"""
import os

import allure
import pytest

from services.admin_service import AdminService
from utils.random_util import random_email, random_name
from utils.test_log import log_resource_ids, log_step_data, log_step_result

# Admin API 创建成员：须含字母与数字，长度大于 8
ADMIN_API_MEMBER_PASSWORD = "AdminApi99x"

# Admin API 端点（可从环境变量 ADMIN_API_BASE_URL 覆盖）
ADMIN_API_BASE_URL = os.getenv("ADMIN_API_BASE_URL", "https://enterprise-platform.dify.dev/admin-api/v1")

# Import DSL 默认 YAML（test_data/recources）；可通过 ADMIN_API_DSL_IMPORT_YAML 覆盖
_ADMIN_API_DSL_IMPORT_DEFAULT = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "test_data",
        "recources",
        "auto_test_model_credential.yml",
    )
)


@allure.epic("Dify Enterprise")
@allure.feature("Admin API")
@pytest.mark.usefixtures("admin_api_p0_secret_key")
class TestE2ECase5P0:

    @allure.story("Secret Key Lists Workspaces")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_admin_secret_key_workspaces(self, admin_client, admin_api_p0_secret_key):
        """
        1. 使用 secretKey 调用 Admin API GET /workspaces，断言状态码 200 且 response 不为空
        2. 使用 secretKey 调用 Admin API POST /workspaces（name、owner_email）创建工作空间
        3. 使用 secretKey 调用 Admin API GET /workspaces/{workspace_id} 查询工作空间
        4. 使用 secretKey 调用 Admin API PUT /workspaces/{workspace_id}（name、status）修改工作空间
        5. 使用 secretKey 调用 Admin API DELETE /workspaces/{workspace_id} 删除工作空间
        """
        secret_key = self.admin_api_secret_key
        log_resource_ids(secret_key_id=admin_api_p0_secret_key)

        # Step 1: 使用 secret key 调用 Admin API 获取工作空间列表
        with allure.step("Step1: 使用 secret key 调用 Admin API 获取工作空间列表"):
            log_step_data("admin api list workspaces params", base_url=ADMIN_API_BASE_URL, page=1, limit=10)
            data = AdminService.list_workspaces_success(
                secret_key,
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            assert data is not None, "response 解析为空"
            log_step_result("admin api workspaces", data)

        # Step 2: Admin API 创建工作空间
        with allure.step("Step2: 使用 secret key 调用 Admin API 创建工作空间 POST /workspaces"):
            owner_email = os.getenv("ADMIN_EMAIL")
            assert owner_email, "需要环境变量 ADMIN_EMAIL 作为 owner_email（须为已存在成员）"
            ws_name = random_name(prefix="admin_api_ws")
            log_step_data(
                "admin api create workspace",
                base_url=ADMIN_API_BASE_URL,
                name=ws_name,
                owner_email=owner_email,
            )
            create_body, workspace_id = AdminService.create_workspace_success(
                secret_key,
                name=ws_name,
                owner_email=owner_email,
                base_url=ADMIN_API_BASE_URL,
            )
            log_resource_ids(workspace_id=workspace_id)
            log_step_result("admin api create workspace", create_body)

        # Step 3: Admin API 查询单个工作空间
        with allure.step("Step3: 使用 secret key 调用 Admin API 查询工作空间 GET /workspaces/{workspace_id}"):
            log_step_data(
                "admin api get workspace",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
            )
            workspace_detail = AdminService.get_workspace_success(
                secret_key,
                workspace_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api get workspace", workspace_detail)

        # Step 4: Admin API 修改工作空间
        with allure.step("Step4: 使用 secret key 调用 Admin API 修改工作空间 PUT /workspaces/{workspace_id}"):
            updated_name = random_name(prefix="admin_api_ws_upd")
            updated_status = "archive"
            log_step_data(
                "admin api update workspace",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                name=updated_name,
                status=updated_status,
            )
            update_body = AdminService.update_workspace_success(
                secret_key,
                workspace_id,
                name=updated_name,
                status=updated_status,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api update workspace", update_body)

        # Step 5: Admin API 删除工作空间
        with allure.step("Step5: 使用 secret key 调用 Admin API 删除工作空间 DELETE /workspaces/{workspace_id}"):
            log_step_data(
                "admin api delete workspace",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
            )
            delete_res = AdminService.delete_workspace_success(
                secret_key,
                workspace_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result(
                "admin api delete workspace",
                {"status_code": delete_res.status_code, "text": (delete_res.text or "")[:500]},
            )

    @allure.story("Secret Key Members")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_admin_secret_key_members(self, admin_client, admin_api_p0_secret_key):
        """
        1. GET /members（page、limit）列举成员
        2. POST /members 创建成员（name、email、password、interface_language、timezone）
        3. GET /members/{member_id} 查询成员
        4. PUT /members/{member_id} 更新成员（name、email、status 等）
        5. DELETE /members/{member_id} 删除成员
        """
        secret_key = self.admin_api_secret_key
        log_resource_ids(secret_key_id=admin_api_p0_secret_key)

        # Step 1: 列举成员
        with allure.step("Step1: 使用 secret key 调用 Admin API 获取成员列表 GET /members"):
            log_step_data(
                "admin api list members params",
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            list_data = AdminService.list_members_success(
                secret_key,
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            assert list_data is not None, "response 解析为空"
            log_step_result("admin api members list", list_data)

        # Step 2: 创建成员
        with allure.step("Step2: 使用 secret key 调用 Admin API 创建成员 POST /members"):
            member_name = random_name(prefix="admin_api_mem")
            member_email = random_email(prefix="admin_api_m")
            log_step_data(
                "admin api create member",
                base_url=ADMIN_API_BASE_URL,
                name=member_name,
                email=member_email,
                interface_language="en-US",
                timezone="America/New_York",
            )
            create_body, member_id = AdminService.create_member_success(
                secret_key,
                name=member_name,
                email=member_email,
                password=ADMIN_API_MEMBER_PASSWORD,
                base_url=ADMIN_API_BASE_URL,
                interface_language="en-US",
                timezone="America/New_York",
            )
            log_resource_ids(member_id=member_id)
            log_step_result("admin api create member", create_body)

        # Step 3: 查询成员
        with allure.step("Step3: 使用 secret key 调用 Admin API 查询成员 GET /members/{member_id}"):
            log_step_data(
                "admin api get member",
                base_url=ADMIN_API_BASE_URL,
                member_id=member_id,
            )
            member_detail = AdminService.get_member_success(
                secret_key,
                member_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api get member", member_detail)

        # Step 4: 更新成员
        with allure.step("Step4: 使用 secret key 调用 Admin API 更新成员 PUT /members/{member_id}"):
            updated_name = random_name(prefix="admin_api_mem_upd")
            updated_email = random_email(prefix="admin_api_m2")
            log_step_data(
                "admin api update member",
                base_url=ADMIN_API_BASE_URL,
                member_id=member_id,
                name=updated_name,
                email=updated_email,
                status="banned",
                interface_language="en-US",
                timezone="America/New_York",
            )
            update_body = AdminService.update_member_success(
                secret_key,
                member_id,
                base_url=ADMIN_API_BASE_URL,
                name=updated_name,
                email=updated_email,
                status="banned",
                interface_language="en-US",
                timezone="America/New_York",
            )
            log_step_result("admin api update member", update_body)

        # Step 5: 删除成员
        with allure.step("Step5: 使用 secret key 调用 Admin API 删除成员 DELETE /members/{member_id}"):
            log_step_data(
                "admin api delete member",
                base_url=ADMIN_API_BASE_URL,
                member_id=member_id,
            )
            delete_res = AdminService.delete_member_success(
                secret_key,
                member_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result(
                "admin api delete member",
                {"status_code": delete_res.status_code, "text": (delete_res.text or "")[:500]},
            )

    @allure.story("Workspace Member")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_admin_workspace_members(
        self,
        admin_client,
        admin_api_p0_secret_key,
        created_member_workspace,
        resource_tracker,
    ):
        """
        前置：created_member_workspace 创建 owner 成员与工作空间。
        1. List / Get Workspace Members（前置工作空间内成员）
        2. Admin API 创建新成员，加入该工作空间，workspace_role=normal
        3. List Workspace Members
        4. Update Workspace Member：将 step2 成员角色改为 admin
        5. Delete Workspace Member：移除 step2 成员
        后置：fixture 清理工作空间与 owner 成员；finally 中删除 step2 创建的成员账号（若仍存在）。
        """
        secret_key = self.admin_api_secret_key
        owner_info, workspace_id = created_member_workspace
        owner_member_id = owner_info["id"]
        assert owner_member_id and workspace_id, "created_member_workspace 应返回 owner member_id 与 workspace_id"
        log_resource_ids(
            secret_key_id=admin_api_p0_secret_key,
            workspace_id=workspace_id,
            member_id=owner_member_id,
        )
        # Step 1: List + Get Workspace Members
        with allure.step("Step1: List / Get Workspace Members GET /workspaces/{workspace_id}/members"):
            log_step_data(
                "admin api list workspace members",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                page=1,
                limit=10,
            )
            list_first = AdminService.list_workspace_members_success(
                secret_key,
                workspace_id,
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            log_step_result("admin api workspace members list (step1)", list_first)

            log_step_data(
                "admin api get workspace member",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                member_id=owner_member_id,
            )
            owner_ws_member = AdminService.get_workspace_member_success(
                secret_key,
                workspace_id,
                owner_member_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api get workspace member (owner)", owner_ws_member)

        # Step 2: 创建成员并加入工作空间 role=normal
        with allure.step(
            "Step2: 创建成员并 Add Workspace Member（workspace_role=normal） POST /workspaces/{workspace_id}/members"
        ):
            join_name = random_name(prefix="admin_api_ws_mem")
            join_email = random_email(prefix="admin_api_wm")
            log_step_data(
                "admin api create member for workspace",
                name=join_name,
                email=join_email,
            )
            _create_body, extra_member_id = AdminService.create_member_success(
                secret_key,
                name=join_name,
                email=join_email,
                password=ADMIN_API_MEMBER_PASSWORD,
                base_url=ADMIN_API_BASE_URL,
            )
            log_resource_ids(join_member_id=extra_member_id)
            resource_tracker.add_member(extra_member_id)
            log_step_result("admin api create member for workspace", _create_body)

            log_step_data(
                "admin api add workspace member",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                member_id=extra_member_id,
                workspace_role="normal",
            )
            add_body = AdminService.add_workspace_member_success(
                secret_key,
                workspace_id,
                extra_member_id,
                workspace_role="normal",
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api add workspace member", add_body)

        # Step 3: List Workspace Members
        with allure.step("Step3: List Workspace Members GET /workspaces/{workspace_id}/members"):
            log_step_data(
                "admin api list workspace members after add",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                page=1,
                limit=10,
            )
            list_after_add = AdminService.list_workspace_members_success(
                secret_key,
                workspace_id,
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            log_step_result("admin api workspace members list (step3)", list_after_add)

        # Step 4: Update Workspace Member -> admin
        with allure.step(
            "Step4: Update Workspace Member PUT /workspaces/{workspace_id}/members/{member_id}（workspace_role=admin）"
        ):
            log_step_data(
                "admin api update workspace member",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                member_id=extra_member_id,
                workspace_role="admin",
            )
            upd_body = AdminService.update_workspace_member_success(
                secret_key,
                workspace_id,
                extra_member_id,
                workspace_role="admin",
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api update workspace member", upd_body)

        # Step 5: Delete Workspace Member
        with allure.step(
            "Step5: Delete Workspace Member DELETE /workspaces/{workspace_id}/members/{member_id}"
        ):
            log_step_data(
                "admin api delete workspace member",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                member_id=extra_member_id,
            )
            del_ws_mem_res = AdminService.delete_workspace_member_success(
                secret_key,
                workspace_id,
                extra_member_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result(
                "admin api delete workspace member",
                {
                    "status_code": del_ws_mem_res.status_code,
                    "text": (del_ws_mem_res.text or "")[:500],
                },
            )

    @allure.story("Group Member")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_admin_secret_key_group_member(self, admin_client, admin_api_p0_secret_key, created_member):
        """
        前置：created_member 创建成员（teardown 时删除该成员）。
        1. List Group GET /groups
        2. Create a Group POST /groups
        3. Update a Group PUT /groups/{group_id}
        4. Get a Group GET /groups/{group_id}
        5. Add Group Member POST /groups/{group_id}/members（member_id 为前置成员）
        6. List Group Members GET /groups/{group_id}/members
        7. Delete Group Member DELETE /groups/{group_id}/members/{member_id}
        8. Delete a Group DELETE /groups/{group_id}
        """
        secret_key = self.admin_api_secret_key
        member_id = created_member["id"]
        assert member_id, "created_member 应包含 id"
        log_resource_ids(secret_key_id=admin_api_p0_secret_key, member_id=member_id)

        with allure.step("Step1: List Group GET /groups"):
            log_step_data(
                "admin api list groups params",
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            list_data = AdminService.list_groups_success(
                secret_key,
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            assert list_data is not None
            log_step_result("admin api groups list", list_data)

        with allure.step("Step2: Create a Group POST /groups"):
            group_name = random_name(prefix="admin_api_grp")
            log_step_data("admin api create group", base_url=ADMIN_API_BASE_URL, name=group_name)
            create_body, group_id = AdminService.create_group_success(
                secret_key,
                name=group_name,
                base_url=ADMIN_API_BASE_URL,
            )
            log_resource_ids(group_id=group_id)
            log_step_result("admin api create group", create_body)

        updated_name = random_name(prefix="admin_api_grp_upd")
        with allure.step("Step3: Update a Group PUT /groups/{group_id}"):
            log_step_data(
                "admin api update group",
                base_url=ADMIN_API_BASE_URL,
                group_id=group_id,
                name=updated_name,
            )
            update_body = AdminService.update_group_success(
                secret_key,
                group_id,
                name=updated_name,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api update group", update_body)

        with allure.step("Step4: Get a Group GET /groups/{group_id}"):
            log_step_data(
                "admin api get group",
                base_url=ADMIN_API_BASE_URL,
                group_id=group_id,
            )
            get_body = AdminService.get_group_success(
                secret_key,
                group_id,
                base_url=ADMIN_API_BASE_URL,
            )
            g = get_body.get("group") if isinstance(get_body.get("group"), dict) else get_body
            assert isinstance(g, dict) and g.get("name") == updated_name, (
                f"Get 返回 name 应与更新后一致: {get_body}"
            )
            log_step_result("admin api get group", get_body)

        with allure.step("Step5: Add Group Member POST /groups/{group_id}/members"):
            log_step_data(
                "admin api add group member",
                base_url=ADMIN_API_BASE_URL,
                group_id=group_id,
                member_id=member_id,
            )
            add_gm_body = AdminService.add_group_member_success(
                secret_key,
                group_id,
                member_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api add group member", add_gm_body)

        with allure.step("Step6: List Group Members GET /groups/{group_id}/members"):
            log_step_data(
                "admin api list group members",
                base_url=ADMIN_API_BASE_URL,
                group_id=group_id,
                page=1,
                limit=10,
            )
            list_gm = AdminService.list_group_members_success(
                secret_key,
                group_id,
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            log_step_result("admin api list group members", list_gm)

        with allure.step("Step7: Delete Group Member DELETE /groups/{group_id}/members/{member_id}"):
            log_step_data(
                "admin api delete group member",
                base_url=ADMIN_API_BASE_URL,
                group_id=group_id,
                member_id=member_id,
            )
            del_gm_res = AdminService.delete_group_member_success(
                secret_key,
                group_id,
                member_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result(
                "admin api delete group member",
                {"status_code": del_gm_res.status_code, "text": (del_gm_res.text or "")[:500]},
            )

        with allure.step("Step8: Delete a Group DELETE /groups/{group_id}"):
            log_step_data("admin api delete group", base_url=ADMIN_API_BASE_URL, group_id=group_id)
            delete_res = AdminService.delete_group_success(
                secret_key,
                group_id,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result(
                "admin api delete group",
                {"status_code": delete_res.status_code, "text": (delete_res.text or "")[:500]},
            )

    @allure.story("Workspace App DSL")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_admin_workspace_dsl_import_export(
        self,
        admin_client,
        admin_api_p0_secret_key,
        created_member_workspace,
    ):
        """
        工作空间应用 DSL：前置 created_member_workspace 提供 owner 邮箱与工作空间 id。
        Step1：Import App DSL（multipart：file、creator_email、name、description）。
        Step2：Export App DSL GET /apps/{app_id}/dsl?include_secret=false。
        """
        secret_key = self.admin_api_secret_key
        member_info, workspace_id = created_member_workspace
        creator_email = member_info.get("email")
        assert creator_email and workspace_id, "created_member_workspace 应返回 member email 与 workspace_id"

        _IMPORT_APP_BASE = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
            "test_data",
        )
        dsl_file = os.path.join(_IMPORT_APP_BASE, "auto_test_model_credential.yml")

        assert os.path.isfile(dsl_file), f"DSL 文件不存在: {dsl_file}"

        app_name = random_name(prefix="admin_api_dsl")
        app_description = f"{random_name(prefix='dsl_desc')}description"

        log_resource_ids(
            secret_key_id=admin_api_p0_secret_key,
            workspace_id=workspace_id,
            member_email=creator_email,
            dsl_file=dsl_file,
        )

        with allure.step("Step1: Import App DSL "):
            log_step_data(
                "admin api import workspace dsl",
                base_url=ADMIN_API_BASE_URL,
                workspace_id=workspace_id,
                creator_email=creator_email,
                name=app_name,
                description=app_description,
                file=dsl_file,
            )
            import_body = AdminService.import_workspace_dsl_success(
                secret_key,
                workspace_id,
                creator_email=creator_email,
                name=app_name,
                description=app_description,
                file_path=dsl_file,
                base_url=ADMIN_API_BASE_URL,
            )
            log_step_result("admin api import workspace dsl", import_body)

            app_id = AdminService._app_id_from_import_dsl_reply(import_body)
            assert app_id, f"导入 DSL 响应中未解析到 app_id: {import_body}"
            log_resource_ids(app_id=app_id)

        with allure.step("Step2: Export App DSL"):
            log_step_data(
                "admin api export app dsl",
                base_url=ADMIN_API_BASE_URL,
                app_id=app_id,
                include_secret=False,
            )
            export_res = AdminService.export_app_dsl_success(
                secret_key,
                app_id,
                base_url=ADMIN_API_BASE_URL,
                include_secret=False,
            )
            dsl_text = export_res.text or ""
            log_step_result(
                "admin api export app dsl",
                {
                    "content_type": export_res.headers.get("Content-Type", ""),
                    "body_length": len(dsl_text),
                    "body_preview": dsl_text[:800],
                },
            )
