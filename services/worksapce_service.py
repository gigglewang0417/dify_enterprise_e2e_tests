from api.workspace_api import (
    create_workspace,
    update_workspace,
    delete_default_workspace,
    delete_workspace,
    get_default_workspace,
    get_workspace,
    get_workspace_permission,
    join_workspace,
    set_default_workspace,
    update_workspace_permission,
)
from services.base_service import BaseService


class WorkspaceService(BaseService):

    def create_workspace_response(self, name, status="normal", email=None, client=None):
        client = self.get_admin_client(client)
        return create_workspace(client, name=name, status=status, email=email)

    def create_workspace_success(self, name, status="normal", email=None, client=None):
        """创建 workspace 成功；若传入 client 则使用（如 fixture admin_client），否则内部 admin_login()。"""
        client = self.get_admin_client(client)
        res = create_workspace(
            client,
            name=name,
            status=status,
            email=email,
        )
        assert res.status_code == 200, f"创建 workspace 失败: {res.status_code}, {res.text[:300]}"
        data = res.json()
        assert "workspace" in data, f"响应中缺少 workspace: {data}"
        workspace = data["workspace"]
        assert workspace.get("id"), "workspace.id 不应为空，创建成功应返回有效 id"
        return workspace

    def get_workspace_success(self, workspace_id, client=None):
        """GET /v1/dashboard/api/workspaces/{id}，EnterpriseWorkspace_GetWorkspace，返回 200 且含 workspace。"""
        client = self.get_admin_client(client)
        res = get_workspace(client, workspace_id)
        data = self.assert_and_parse(res, message="获取 workspace 失败")
        assert "workspace" in data, f"响应中缺少 workspace: {data}"
        workspace = data["workspace"]
        assert workspace.get("id") == workspace_id, f"返回的 workspace.id 应与请求 id 一致: {workspace}"
        return workspace

    def update_workspace_success(self, workspace_id, client=None, name="after_update", status="normal", email="updated@dify.ai"):
        """PUT /v1/dashboard/api/workspaces/{id}，EnterpriseWorkspace_UpdateWorkspace，UpdateWorkspaceReq 必填，返回 200 且含 UpdateWorkspaceReply。"""
        client = self.get_admin_client(client)
        res = update_workspace(
            client,
            workspace_id,
            name=name,
            status=status,
            email=email,
        )
        data = self.assert_and_parse(res, message="修改 workspace 失败")
        assert "workspace" in data, f"响应中缺少 workspace（UpdateWorkspaceReply）: {data}"
        workspace = data["workspace"]
        assert workspace.get("id") == workspace_id
        if name is not None:
            assert workspace.get("name") == name, f"name 应已更新: {workspace}"
        if email is not None:
            owner = workspace.get("owner") or {}
            returned_email = workspace.get("email") or owner.get("email")
            assert returned_email == email, f"email 应已更新: {workspace}"
        if status is not None:
            assert workspace.get("status") == status, f"status 应已更新: {workspace}"
        return workspace

    def update_workspace_response(self, workspace_id, client=None, name=None, status=None, email=None):
        client = self.get_admin_client(client)
        return update_workspace(client, workspace_id, name=name, status=status, email=email)

    def delete_workspace_success(self, workspace_id, client=None):
        """DELETE /v1/dashboard/api/workspaces/{workspace_id}，无 body，返回 200 且响应体为空则删除成功。"""
        client = self.get_admin_client(client)
        res = delete_workspace(client, workspace_id)
        assert res.status_code == 200, f"删除 workspace 失败: {res.status_code}, {res.text[:300]}"
        # 删除成功：响应体为空（无内容或空 JSON）
        body = res.text.strip()
        assert not body or body in ("{}", "null"), f"删除成功时响应体应为空，实际: {res.text[:200]}"

    def set_default_workspace_success(self, workspace_id, client=None, **payload):
        """
        PUT /v1/dashboard/api/workspaces/{id}/default，body 默认 ``{"id": workspace_id}``。
        成功响应含 ``workspaceId``，与请求的 workspace 一致。
        """
        client = self.get_admin_client(client)
        res = set_default_workspace(client, workspace_id, **payload)
        data = self.assert_and_parse(res, message="设置默认 workspace 失败")
        assert isinstance(data, dict), f"设置默认 workspace 响应格式异常: {data}"
        wid = data.get("workspaceId")
        assert wid == workspace_id or str(wid) == str(workspace_id), (
            f"响应 workspaceId 应与请求一致: 期望 {workspace_id}, 实际 {wid}, body: {data}"
        )
        return data

    def get_default_workspace_success(self, client=None):
        """
        GET /v1/dashboard/api/default-workspace。
        断言返回 ``workspaceId`` 与 ``workspace.id`` 一致。
        """
        client = self.get_admin_client(client)
        res = get_default_workspace(client)
        data = self.assert_and_parse(res, message="查询默认 workspace 失败")
        assert isinstance(data, dict), f"默认 workspace 响应格式异常: {data}"
        wid = data.get("workspaceId")
        assert wid, f"响应中缺少 workspaceId: {data}"
        ws = data.get("workspace")
        assert isinstance(ws, dict), f"响应中 workspace 应为对象: {data}"
        assert ws.get("id") == wid or str(ws.get("id")) == str(wid), (
            f"workspace.id 应与 workspaceId 一致: {data}"
        )
        return data

    def delete_default_workspace_success(self, client=None):
        """
        DELETE /v1/dashboard/api/default-workspace。
        成功时 HTTP 200，响应体为空或 ``{}``。
        """
        client = self.get_admin_client(client)
        res = delete_default_workspace(client)
        assert res.status_code == 200, (
            f"取消默认 workspace 失败: {res.status_code}, {res.text[:300]}"
        )
        body = res.text.strip()
        assert not body or body in ("{}", "null"), (
            f"取消默认 workspace 成功时响应体应为空或 {{}}，实际: {res.text[:200]}"
        )
        return self.parse_json(res)

    def join_workspace_success(self, workspace_id, client=None, **payload):
        client = self.get_admin_client(client)
        res = join_workspace(client, workspace_id, **payload)
        return self.assert_and_parse(res, message="加入 workspace 成员失败")

    def join_workspace_response(self, workspace_id, client=None, **payload):
        client = self.get_admin_client(client)
        return join_workspace(client, workspace_id, **payload)

    def get_workspace_permission_success(self, workspace_id, client=None):
        client = self.get_admin_client(client)
        res = get_workspace_permission(client, workspace_id)
        data = self.assert_and_parse(res, message="查询 workspace 权限失败")
        assert isinstance(data, dict), f"workspace 权限响应格式异常: {data}"
        assert "permission" in data, f"响应中缺少 permission: {data}"
        perm = data.get("permission")
        assert isinstance(perm, dict), f"permission 应为对象: {data}"
        wid = perm.get("workspaceId")
        assert wid == workspace_id or str(wid) == str(workspace_id), (
            f"permission.workspaceId 应与请求 workspace 一致: 期望 {workspace_id}, 实际 {wid}"
        )
        for key in ("allowMemberInvite", "allowOwnerTransfer"):
            if key in perm:
                assert isinstance(perm[key], bool), (
                    f"{key} 应为布尔值: {perm}"
                )
        return data

    def update_workspace_permission_success(
        self,
        workspace_id,
        client=None,
        *,
        permission_body=None,
        **payload,
    ):
        client = self.get_admin_client(client)
        if permission_body is not None:
            if payload:
                raise ValueError(
                    "请只使用其一：permission_body（自动组 body）或 **payload（完整 body），不要同时传入"
                )
            body = {
                "id": workspace_id,
                "permission": {
                    "workspaceId": workspace_id,
                    **permission_body,
                },
            }
        else:
            body = payload
        res = update_workspace_permission(client, workspace_id, **body)
        data = self.assert_and_parse(res, message="更新 workspace 权限失败")
        assert isinstance(data, dict), f"workspace 权限更新响应格式异常: {data}"
        if data.get("message") is not None:
            assert data.get("message") == "success", (
                f"更新权限应返回 message=success: {data}"
            )
        assert "permission" in data, f"响应中缺少 permission: {data}"
        perm = data.get("permission") or {}
        assert perm.get("workspaceId") == workspace_id or str(perm.get("workspaceId")) == str(
            workspace_id
        ), f"permission.workspaceId 应与 workspace 一致: {data}"
        return data
