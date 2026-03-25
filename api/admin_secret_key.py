from common.config import config

# 路径常量（与 OpenAPI AdminSecretKey 一致）
ADMIN_SECRET_KEYS_BASE_PATH = f"{config.base_url}/dashboard/api/admin-secret-keys"


def _secret_key_by_id_path(secret_key_id):
    return f"{ADMIN_SECRET_KEYS_BASE_PATH}/{secret_key_id}"


def list_secret_keys(
    client,
    status=None,
    page_number=None,
    results_per_page=None,
    reverse=None,
):
    """
    GET /v1/dashboard/api/admin-secret-keys
    AdminSecretKey_ListSecretKeys
    query: status, pageNumber, resultsPerPage, reverse
    response: ListSecretKeysReply
    """
    params = {}
    if status is not None:
        params["status"] = status
    if page_number is not None:
        params["pageNumber"] = page_number
    if results_per_page is not None:
        params["resultsPerPage"] = results_per_page
    if reverse is not None:
        params["reverse"] = reverse
    return client.get(ADMIN_SECRET_KEYS_BASE_PATH, params=params if params else None)


def create_secret_key(client, **payload):
    """
    POST /v1/dashboard/api/admin-secret-keys
    AdminSecretKey_CreateSecretKey
    requestBody: CreateSecretKeyReq (required)
    response: CreateSecretKeyReply
    """
    return client.post(ADMIN_SECRET_KEYS_BASE_PATH, json=payload)


def delete_secret_key(client, secret_key_id):
    """
    DELETE /v1/dashboard/api/admin-secret-keys/{id}
    AdminSecretKey_DeleteSecretKey
    response: DeleteSecretKeyReply
    """
    path = _secret_key_by_id_path(secret_key_id)
    return client.delete(path)
