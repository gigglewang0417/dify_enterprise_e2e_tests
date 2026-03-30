"""
Admin API：使用 secret key（Bearer）调用的接口，base 为 ADMIN_API_BASE_URL（如 https://xxx/admin-api/v1）
"""
import os

import requests

from common.config import config


def _admin_api_base(base_url=None):
    base = (base_url or getattr(config, "admin_api_base_url", None) or os.getenv("ADMIN_API_BASE_URL") or "").rstrip("/")
    return base


def _workspace_dsl_import_url(admin_base, workspace_id):
    """
    与 Postman 一致：``{{base_url}}/admin-api/v1/workspaces/{{workspaceId}}/dsl/import``

    - 若 ``admin_base`` 已以 ``/admin-api/v1`` 结尾（如默认 ADMIN_API_BASE_URL），则只追加 ``/workspaces/...``。
    - 若仅为站点根（``https://host``），则自动补上 ``/admin-api/v1`` 段。
    """
    base = (admin_base or "").rstrip("/")
    ws = str(workspace_id).strip("/")
    if not base:
        return f"/admin-api/v1/workspaces/{ws}/dsl/import"
    if base.endswith("/admin-api/v1"):
        return f"{base}/workspaces/{ws}/dsl/import"
    return f"{base}/admin-api/v1/workspaces/{ws}/dsl/import"


def _app_dsl_export_url(admin_base, app_id):
    """
    与 Postman 一致：``{{base_url}}/admin-api/v1/apps/{{app_id}}/dsl``
    """
    base = (admin_base or "").rstrip("/")
    aid = str(app_id).strip("/")
    if not base:
        return f"/admin-api/v1/apps/{aid}/dsl"
    if base.endswith("/admin-api/v1"):
        return f"{base}/apps/{aid}/dsl"
    return f"{base}/admin-api/v1/apps/{aid}/dsl"


def list_workspaces(
    secret_key,
    base_url=None,
    name=None,
    status=None,
    page=1,
    limit=10,
):
    """
    GET {admin_api_base}/workspaces
    使用 Admin API secret key（Bearer）鉴权，获取工作空间列表。
    query: name, status, page, limit
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces"
    params = {}
    if name is not None:
        params["name"] = name
    if status is not None:
        params["status"] = status
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, params=params if params else None, headers=headers)


def create_workspace(secret_key, name, owner_email, base_url=None):
    """
    POST {admin_api_base}/workspaces
    使用 Admin API secret key（Bearer）鉴权，创建工作空间。
    requestBody: {"name": "...", "owner_email": "..."}（owner 须为已存在成员邮箱）
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    body = {"name": name, "owner_email": owner_email}
    return requests.post(url, json=body, headers=headers)


def get_workspace(secret_key, workspace_id, base_url=None):
    """
    GET {admin_api_base}/workspaces/{workspace_id}
    使用 Admin API secret key（Bearer）鉴权，获取单个工作空间。
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, headers=headers)


def update_workspace(secret_key, workspace_id, name, status, base_url=None):
    """
    PUT {admin_api_base}/workspaces/{workspace_id}
    使用 Admin API secret key（Bearer）鉴权，修改工作空间。
    requestBody: {"name": "...", "status": "normal" | "archive"}
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    body = {"name": name, "status": status}
    return requests.put(url, json=body, headers=headers)


def delete_workspace(secret_key, workspace_id, base_url=None):
    """
    DELETE {admin_api_base}/workspaces/{workspace_id}
    使用 Admin API secret key（Bearer）鉴权，删除工作空间。
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.delete(url, headers=headers)


def list_members(
    secret_key,
    base_url=None,
    name=None,
    email=None,
    status=None,
    page=1,
    limit=10,
):
    """
    GET {admin_api_base}/members
    query: name, email, status（可选），page（默认 1）, limit（默认 10）
    """
    base = _admin_api_base(base_url)
    url = f"{base}/members"
    params = {}
    if name is not None:
        params["name"] = name
    if email is not None:
        params["email"] = email
    if status is not None:
        params["status"] = status
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, params=params if params else None, headers=headers)


def create_member(
    secret_key,
    name,
    email,
    base_url=None,
    password=None,
    interface_language="en-US",
    timezone="America/New_York",
):
    """
    POST {admin_api_base}/members
    body: name, email, password（可选）, interface_language, timezone
    """
    base = _admin_api_base(base_url)
    url = f"{base}/members"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    body = {
        "name": name,
        "email": email,
        "interface_language": interface_language,
        "timezone": timezone,
    }
    if password is not None:
        body["password"] = password
    return requests.post(url, json=body, headers=headers)


def get_member(secret_key, member_id, base_url=None):
    """GET {admin_api_base}/members/{member_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/members/{member_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, headers=headers)


def update_member(
    secret_key,
    member_id,
    base_url=None,
    name=None,
    email=None,
    status=None,
    password=None,
    interface_language=None,
    timezone=None,
):
    """
    PUT {admin_api_base}/members/{member_id}
    body 字段均为可选，仅传需要修改的字段。
    """
    base = _admin_api_base(base_url)
    url = f"{base}/members/{member_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    body = {}
    if name is not None:
        body["name"] = name
    if email is not None:
        body["email"] = email
    if status is not None:
        body["status"] = status
    if password is not None:
        body["password"] = password
    if interface_language is not None:
        body["interface_language"] = interface_language
    if timezone is not None:
        body["timezone"] = timezone
    return requests.put(url, json=body, headers=headers)


def delete_member(secret_key, member_id, base_url=None):
    """DELETE {admin_api_base}/members/{member_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/members/{member_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.delete(url, headers=headers)


def list_workspace_members(
    secret_key,
    workspace_id,
    base_url=None,
    workspace_role=None,
    page=1,
    limit=10,
):
    """
    GET {admin_api_base}/workspaces/{workspace_id}/members
    query: workspace_role（可选）, page, limit
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}/members"
    params = {}
    if workspace_role is not None:
        params["workspace_role"] = workspace_role
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, params=params if params else None, headers=headers)


def get_workspace_member(secret_key, workspace_id, member_id, base_url=None):
    """GET {admin_api_base}/workspaces/{workspace_id}/members/{member_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}/members/{member_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, headers=headers)


def add_workspace_member(secret_key, workspace_id, member_id, workspace_role, base_url=None):
    """
    POST {admin_api_base}/workspaces/{workspace_id}/members
    body: member_id, workspace_role（owner / admin / editor / normal）
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}/members"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    body = {"member_id": member_id, "workspace_role": workspace_role}
    return requests.post(url, json=body, headers=headers)


def update_workspace_member(secret_key, workspace_id, member_id, workspace_role, base_url=None):
    """PUT {admin_api_base}/workspaces/{workspace_id}/members/{member_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}/members/{member_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    body = {"workspace_role": workspace_role}
    return requests.put(url, json=body, headers=headers)


def delete_workspace_member(secret_key, workspace_id, member_id, base_url=None):
    """DELETE {admin_api_base}/workspaces/{workspace_id}/members/{member_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces/{workspace_id}/members/{member_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.delete(url, headers=headers)


def list_groups(secret_key, base_url=None, name=None, page=1, limit=10):
    """
    GET {admin_api_base}/groups
    query: name（可选）, page, limit
    """
    base = _admin_api_base(base_url)
    url = f"{base}/groups"
    params = {}
    if name is not None:
        params["name"] = name
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, params=params if params else None, headers=headers)


def create_group(secret_key, name, base_url=None):
    """POST {admin_api_base}/groups，body: {\"name\": \"...\"}"""
    base = _admin_api_base(base_url)
    url = f"{base}/groups"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.post(url, json={"name": name}, headers=headers)


def get_group(secret_key, group_id, base_url=None):
    """GET {admin_api_base}/groups/{group_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/groups/{group_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, headers=headers)


def update_group(secret_key, group_id, name, base_url=None):
    """PUT {admin_api_base}/groups/{group_id}，body: {\"name\": \"...\"}"""
    base = _admin_api_base(base_url)
    url = f"{base}/groups/{group_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.put(url, json={"name": name}, headers=headers)


def delete_group(secret_key, group_id, base_url=None):
    """DELETE {admin_api_base}/groups/{group_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/groups/{group_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.delete(url, headers=headers)


def list_group_members(secret_key, group_id, base_url=None, page=1, limit=10):
    """
    GET {admin_api_base}/groups/{group_id}/members
    query: page, limit
    """
    base = _admin_api_base(base_url)
    url = f"{base}/groups/{group_id}/members"
    params = {}
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, params=params if params else None, headers=headers)


def add_group_member(secret_key, group_id, member_id, base_url=None):
    """
    POST {admin_api_base}/groups/{group_id}/members
    body: {\"member_id\": \"...\"}
    """
    base = _admin_api_base(base_url)
    url = f"{base}/groups/{group_id}/members"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.post(url, json={"member_id": member_id}, headers=headers)


def delete_group_member(secret_key, group_id, member_id, base_url=None):
    """DELETE {admin_api_base}/groups/{group_id}/members/{member_id}"""
    base = _admin_api_base(base_url)
    url = f"{base}/groups/{group_id}/members/{member_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.delete(url, headers=headers)


def import_workspace_dsl(
    secret_key,
    workspace_id,
    creator_email,
    name,
    description,
    file_path,
    base_url=None,
):
    """
    Postman「Import DSL」：POST multipart/form-data。

    URL 与 Postman ``{{base_url}}/admin-api/v1/workspaces/:workspaceId/dsl/import`` 一致，
    由 ``_workspace_dsl_import_url`` 根据是否已含 ``/admin-api/v1`` 拼接。

    form 字段：file（文件）、creator_email、name、description（文本）。
    请求头仅设 Bearer；不设 Content-Type，以便 requests 生成 multipart boundary。
    """
    admin_base = _admin_api_base(base_url)
    url = _workspace_dsl_import_url(admin_base, workspace_id)
    headers = {"Authorization": f"Bearer {secret_key}"}
    data = {
        "creator_email": creator_email,
        "name": name,
        "description": description,
    }
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as fp:
        files = {"file": (filename, fp, "application/octet-stream")}
        return requests.post(url, headers=headers, data=data, files=files)


def export_app_dsl(secret_key, app_id, base_url=None, include_secret=False):
    """
    Postman「Export DSL」：GET，query ``include_secret`` 为 ``true`` / ``false`` 字符串。
    """
    admin_base = _admin_api_base(base_url)
    url = _app_dsl_export_url(admin_base, app_id)
    headers = {"Authorization": f"Bearer {secret_key}"}
    params = {"include_secret": "true" if include_secret else "false"}
    return requests.get(url, headers=headers, params=params)
