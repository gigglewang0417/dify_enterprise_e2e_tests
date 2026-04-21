from common.config import config

# 路径常量（与 OpenAPI EnterpriseWorkspace 一致）
_DASHBOARD_API_BASE = f"{config.base_url}/dashboard/api"
WORKSPACE_BASE_PATH = f"{_DASHBOARD_API_BASE}/workspaces"
WORKSPACE_CREATE_PATH = WORKSPACE_BASE_PATH
DEFAULT_WORKSPACE_PATH = f"{_DASHBOARD_API_BASE}/default-workspace"


def _workspace_by_id_path(workspace_id):
    return f"{WORKSPACE_BASE_PATH}/{workspace_id}"


def create_workspace_payload(name, status="normal", email=None):
    """CreateWorkspaceReq 请求体，供 Client 调用时使用。"""
    return {
        "name": name,
        "status": status,
        "email": email or "",
    }

def create_workspace(client, name, status="normal", email=None):
    """使用已登录的 Client 创建 workspace。"""
    payload = create_workspace_payload(name=name, status=status, email=email)
    return client.post(WORKSPACE_CREATE_PATH, json=payload)


def get_workspace(client, workspace_id):
    """
    GET /v1/dashboard/api/workspaces/{id}
    EnterpriseWorkspace_GetWorkspace
    """
    path = _workspace_by_id_path(workspace_id)
    return client.get(path)


def update_workspace(client, workspace_id, name=None, status=None, email=None):
    """
    PUT /v1/dashboard/api/workspaces/{id}
    EnterpriseWorkspace_UpdateWorkspace
    UpdateWorkspaceReq：只传需要更新的字段即可。
    """
    path = _workspace_by_id_path(workspace_id)
    payload = {}
    if name is not None:
        payload["name"] = name
    if status is not None:
        payload["status"] = status
    if email is not None:
        payload["email"] = email
    if workspace_id is not None:
        payload["id"] = workspace_id
    return client.put(path, json=payload)


def delete_workspace(admin_client, workspace_id):
    """
    DELETE /v1/dashboard/api/workspaces/{id}
    EnterpriseWorkspace_DeleteWorkspace
    """
    path = _workspace_by_id_path(workspace_id)
    return admin_client.delete(path)


def set_default_workspace(client, workspace_id, **payload):
    """
    PUT /v1/dashboard/api/workspaces/{id}/default
    EnterpriseWorkspace_SetDefaultWorkspace
    requestBody 示例: {"id": "<workspace_id>"}
    response 示例: {"workspaceId": "<workspace_id>"}
    """
    path = f"{_workspace_by_id_path(workspace_id)}/default"
    body = payload if payload else {"id": workspace_id}
    return client.put(path, json=body)


def get_default_workspace(client):
    """
    GET /v1/dashboard/api/default-workspace
    查询当前用户的默认工作空间。
    response 示例: {"workspaceId": "...", "workspace": {"id", "name", "status", "owner", ...}}
    """
    return client.get(DEFAULT_WORKSPACE_PATH)


def delete_default_workspace(client):
    """
    DELETE /v1/dashboard/api/default-workspace
    取消当前用户的默认工作空间设置。
    response 示例: {}（空 JSON）
    """
    return client.delete(DEFAULT_WORKSPACE_PATH)


def join_workspace(client, workspace_id, **payload):
    """
    POST /v1/dashboard/api/workspaces/{id}/member
    EnterpriseWorkspace_JoinWorkspace
    requestBody: JoinWorkspaceReq (required)
    """
    path = f"{_workspace_by_id_path(workspace_id)}/member"
    return client.post(path, json=payload)


def get_workspace_permission(client, workspace_id):
    """
    GET /v1/dashboard/api/workspaces/{id}/permission
    EnterpriseWorkspace_GetWorkspacePermission
    """
    path = f"{_workspace_by_id_path(workspace_id)}/permission"
    return client.get(path)


def update_workspace_permission(client, workspace_id, **payload):
    """
    POST /v1/dashboard/api/workspaces/{id}/permission
    EnterpriseWorkspace_UpdateWorkspacePermission
    requestBody: UpdateWorkspacePermissionReq (required)
    """
    path = f"{_workspace_by_id_path(workspace_id)}/permission"
    return client.post(path, json=payload)

