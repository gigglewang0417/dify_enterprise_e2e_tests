from common.config import config

# 路径常量（与 OpenAPI PluginManagerCredential 一致）
CREDENTIALS_BASE_PATH = f"{config.base_url}/plugin-manager/credentials"
CREDENTIALS_DELETE_WITH_USAGE_CHECK_PATH = f"{config.base_url}/plugin-manager/credentials/delete-with-usage-check"
CREDENTIAL_TENANT_JOINS_PATH = f"{config.base_url}/plugin-manager/credential-tenant-joins"
CREDENTIAL_TENANT_JOINS_OPERATE_PATH = f"{config.base_url}/plugin-manager/credential-tenant-joins/operate"

# PluginManagerCredentialPolicy
CREDENTIAL_POLICIES_BASE_PATH = f"{config.base_url}/plugin-manager/credential-policies"
CREDENTIAL_POLICIES_CHECK_PATH = f"{config.base_url}/plugin-manager/credential-policies/check"


def _credential_by_id_path(credential_id):
    return f"{CREDENTIALS_BASE_PATH}/{credential_id}"


def list_credentials(
    client,
    search=None,
    credential_type=None,
    page_number=None,
    results_per_page=None,
    reverse=None,
):
    """
    GET /v1/plugin-manager/credentials
    PluginManagerCredential_ListCredentials
    query: search, type, pageNumber, resultsPerPage, reverse
    response: ListCredentialsReply
    """
    params = {}
    if search is not None:
        params["search"] = search
    if credential_type is not None:
        params["type"] = credential_type
    if page_number is not None:
        params["pageNumber"] = page_number
    if results_per_page is not None:
        params["resultsPerPage"] = results_per_page
    if reverse is not None:
        params["reverse"] = reverse
    return client.get(CREDENTIALS_BASE_PATH, params=params if params else None)


def create_credential(client, **payload):
    """
    POST /v1/plugin-manager/credentials
    PluginManagerCredential_CreateCredential
    requestBody: CreateCredentialRequest (required)
    response: CreateCredentialReply
    """
    return client.post(CREDENTIALS_BASE_PATH, json=payload)


def get_credential(client, credential_id):
    """
    GET /v1/plugin-manager/credentials/{id}
    PluginManagerCredential_GetCredential
    response: GetCredentialReply
    """
    path = _credential_by_id_path(credential_id)
    return client.get(path)


def update_credential(client, credential_id, **payload):
    """
    PUT /v1/plugin-manager/credentials/{id}
    PluginManagerCredential_UpdateCredential
    requestBody: UpdateCredentialRequest (required)
    response: UpdateCredentialReply
    """
    path = _credential_by_id_path(credential_id)
    return client.put(path, json=payload)


def delete_credential(client, credential_id, **payload):
    """
    DELETE /v1/plugin-manager/credentials/{id}
    PluginManagerCredential_DeleteCredential
    requestBody: DeleteCredentialRequest (required)
    response: DeleteCredentialReply
    """
    path = _credential_by_id_path(credential_id)
    return client.delete(path, json=payload if payload else {})


def delete_credential_with_usage_check(client, **payload):
    """
    POST /v1/plugin-manager/credentials/delete-with-usage-check
    删除凭据（带使用校验），requestBody: {"id": "credential_id"}，response: {"items": []}
    """
    return client.post(CREDENTIALS_DELETE_WITH_USAGE_CHECK_PATH, json=payload)


def list_credential_tenant_joins(client, credential_id=None):
    """
    GET /v1/plugin-manager/credential-tenant-joins
    PluginManagerCredentialTenantJoin_ListCredentialTenantJoins
    query: credentialId
    response: ListCredentialTenantJoinsReply
    """
    params = {}
    if credential_id is not None:
        params["credentialId"] = credential_id
    return client.get(CREDENTIAL_TENANT_JOINS_PATH, params=params if params else None)


def create_credential_tenant_join(client, **payload):
    """
    POST /v1/plugin-manager/credential-tenant-joins
    PluginManagerCredentialTenantJoin_CreateCredentialTenantJoin
    requestBody: CreateCredentialTenantJoinRequest (required)
    response: CreateCredentialTenantJoinReply
    """
    return client.post(CREDENTIAL_TENANT_JOINS_PATH, json=payload)


def batch_delete_credential_tenant_joins(client, **payload):
    """
    DELETE /v1/plugin-manager/credential-tenant-joins
    PluginManagerCredentialTenantJoin_BatchDeleteCredentialTenantJoins
    requestBody: BatchDeleteCredentialTenantJoinsRequest (required)
    response: BatchDeleteCredentialTenantJoinsReply
    """
    return client.delete(CREDENTIAL_TENANT_JOINS_PATH, json=payload)


def operate_credential_tenant_joins(client, **payload):
    """
    POST /v1/plugin-manager/credential-tenant-joins/operate
    PluginManagerCredentialTenantJoin_OperateCredentialTenantJoins
    requestBody: OperateCredentialTenantJoinsRequest (required)
    response: OperateCredentialTenantJoinsReply
    """
    return client.post(CREDENTIAL_TENANT_JOINS_OPERATE_PATH, json=payload)


def _credential_policy_by_id_path(policy_id):
    return f"{CREDENTIAL_POLICIES_BASE_PATH}/{policy_id}"


def get_credential_policy(client):
    """
    GET /v1/plugin-manager/credential-policies
    PluginManagerCredentialPolicy_GetCredentialPolicy
    response: GetCredentialPolicyReply
    """
    return client.get(CREDENTIAL_POLICIES_BASE_PATH)


def update_credential_policy(client, **payload):
    """
    PUT /v1/plugin-manager/credential-policies
    PluginManagerCredentialPolicy_UpdateCredentialPolicy
    requestBody: UpdateCredentialPolicyRequest (required)
    response: UpdateCredentialPolicyReply
    """
    return client.put(CREDENTIAL_POLICIES_BASE_PATH, json=payload)


def create_credential_policy(client, **payload):
    """
    POST /v1/plugin-manager/credential-policies
    PluginManagerCredentialPolicy_CreateCredentialPolicy
    requestBody: CreateCredentialPolicyRequest (required)
    response: CreateCredentialPolicyReply
    """
    return client.post(CREDENTIAL_POLICIES_BASE_PATH, json=payload)


def check_credential_policy(client, **payload):
    """
    POST /v1/plugin-manager/credential-policies/check
    PluginManagerCredentialPolicy_CheckCredentialPolicy
    requestBody: CheckCredentialPolicyRequest (required)
    response: CheckCredentialPolicyReply
    """
    return client.post(CREDENTIAL_POLICIES_CHECK_PATH, json=payload)


def delete_credential_policy(client, policy_id, **payload):
    """
    DELETE /v1/plugin-manager/credential-policies/{id}
    PluginManagerCredentialPolicy_DeleteCredentialPolicy
    requestBody: DeleteCredentialPolicyRequest (required)
    response: DeleteCredentialPolicyReply
    """
    path = _credential_policy_by_id_path(policy_id)
    return client.delete(path, json=payload if payload else {})
