from urllib.parse import urlencode

from common.config import config

MEMBER_BASE_PATH = f"{config.base_url}/dashboard/api/members"


def _member_by_id_path(member_id):
    return f"{MEMBER_BASE_PATH}/{member_id}"


def _list_members_path(
    email=None,
    status=None,
    workspace_id=None,
    page_number=1,
    results_per_page=10,
    reverse=True,
    group_name=None,
):
    """拼接 list_members 请求的 path（含 query 参数）。必传/默认：pageNumber=1, resultsPerPage=10, reverse=true。"""
    params = {
        "pageNumber": page_number,
        "resultsPerPage": results_per_page,
        "reverse": "true" if reverse else "false",
    }
    if email is not None:
        params["email"] = email
    if status is not None:
        params["status"] = status
    if workspace_id is not None:
        params["workspaceId"] = workspace_id
    if group_name is not None:
        params["groupName"] = group_name
    return f"{MEMBER_BASE_PATH}?{urlencode(params)}"


def list_members(
    client,
    email=None,
    status=None,
    workspace_id=None,
    page_number=1,
    results_per_page=10,
    reverse=True,
    group_name=None,
):
    """
    GET /v1/dashboard/api/members
    EnterpriseMember_ListMembers
    query: email, status, workspaceId, pageNumber(默认1), resultsPerPage(默认10), reverse(默认true), groupName
    """
    path = _list_members_path(
        email=email,
        status=status,
        workspace_id=workspace_id,
        page_number=page_number,
        results_per_page=results_per_page,
        reverse=reverse,
        group_name=group_name,
    )
    return client.get(path)


def create_member(client, **payload):
    """
    POST /v1/dashboard/api/members
    EnterpriseMember_CreateMember
    requestBody: CreateMemberReq (required)
    """
    return client.post(MEMBER_BASE_PATH, json=payload)


def get_member(client, member_id):
    """
    GET /v1/dashboard/api/members/{id}
    EnterpriseMember_GetMember
    """
    path = _member_by_id_path(member_id)
    return client.get(path)


def update_member(client, member_id, **payload):
    """
    PUT /v1/dashboard/api/members/{id}
    EnterpriseMember_UpdateMember
    requestBody: UpdateMemberReq (required)
    """
    path = _member_by_id_path(member_id)
    return client.put(path, json=payload)


def delete_member(client, member_id):
    """
    DELETE /v1/dashboard/api/members/{id}
    EnterpriseMember_DeleteMember
    """
    path = _member_by_id_path(member_id)
    return client.delete(path)


def reset_member_password(client, member_id, **payload):
    """
    POST /v1/dashboard/api/members/{id}/reset-password
    EnterpriseMember_ResetMemberPassword
    requestBody: ResetMemberPasswordReq (required)
    """
    path = f"{_member_by_id_path(member_id)}/reset-password"
    return client.post(path, json=payload)
