from common.config import config

# 路径常量（与 OpenAPI EnterpriseUser 一致）
USER_BASE_PATH = f"{config.base_url}/dashboard/api/users"


def _user_by_id_path(user_id):
    return f"{USER_BASE_PATH}/{user_id}"


def list_users(
    client,
    email=None,
    status=None,
    page_number=None,
    results_per_page=None,
    reverse=None,
):
    """
    GET /v1/dashboard/api/users
    EnterpriseUser_ListUsers
    query: email, status, pageNumber, resultsPerPage, reverse
    """
    params = {}
    if email is not None:
        params["email"] = email
    if status is not None:
        params["status"] = status
    if page_number is not None:
        params["pageNumber"] = page_number
    if results_per_page is not None:
        params["resultsPerPage"] = results_per_page
    if reverse is not None:
        params["reverse"] = reverse
    return client.get(USER_BASE_PATH, params=params if params else None)


def create_user(client, **payload):
    """
    POST /v1/dashboard/api/users
    EnterpriseUser_CreateUser
    requestBody: CreateUserReq (required)
    """
    return client.post(USER_BASE_PATH, json=payload)


def get_user(client, user_id):
    """
    GET /v1/dashboard/api/users/{id}
    EnterpriseUser_GetUser
    """
    path = _user_by_id_path(user_id)
    return client.get(path)


def update_user(client, user_id, **payload):
    """
    PUT /v1/dashboard/api/users/{id}
    EnterpriseUser_UpdateUser
    requestBody: UpdateUserReq (required)
    """
    path = _user_by_id_path(user_id)
    return client.put(path, json=payload)


def delete_user(client, user_id):
    """
    DELETE /v1/dashboard/api/users/{id}
    EnterpriseUser_DeleteUser
    """
    path = _user_by_id_path(user_id)
    return client.delete(path)


def reset_user_password(client, user_id, **payload):
    """
    POST /v1/dashboard/api/users/{id}/reset-password
    EnterpriseUser_ResetUserPassword
    requestBody: ResetUserPasswordReq (required)
    """
    path = f"{_user_by_id_path(user_id)}/reset-password"
    return client.post(path, json=payload)
