from common.config import config

# 路径常量（与 OpenAPI EnterpriseWorkspace 一致）
WORKSPACE_BASE_PATH = f"{config.base_url}/dashboard/api/workspaces"
WORKSPACE_CREATE_PATH = WORKSPACE_BASE_PATH


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
    requestBody: SetDefaultWorkspaceReq (required)
    """
    path = f"{_workspace_by_id_path(workspace_id)}/default"
    return client.put(path, json=payload if payload else {})


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

