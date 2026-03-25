from common.config import config

# Console：base 使用 CONSOLE_URL（如 https://console-platform.dify.dev）
_CONSOLE_API_BASE = f"{(config.console_url or '').rstrip('/')}/console/api"

# 工作空间内置工具提供商：/console/api/workspaces/current/tool-provider/builtin/{provider_path}/...
_WORKSPACE_TOOL_PROVIDER_BUILTIN_BASE = (
    f"{_CONSOLE_API_BASE}/workspaces/current/tool-provider/builtin"
)

# 工作空间模型提供商：
# GET    {base} — 列表及 schema 等
# POST   {base}/{provider_path}/credentials — 创建凭据
# POST   {base}/{provider_path}/credentials/switch — 切换当前使用的自定义凭据（body: credential_id）
# DELETE {base}/{provider_path}/credentials — 删除凭据（body: credential_id）
_WORKSPACE_MODEL_PROVIDERS_BASE = f"{_CONSOLE_API_BASE}/workspaces/current/model-providers"


def _workspace_tool_provider_builtin_add_path(provider_path):
    """provider_path 例如 langgenius/github/github（不含首尾斜杠）。"""
    p = provider_path.strip("/")
    return f"{_WORKSPACE_TOOL_PROVIDER_BUILTIN_BASE}/{p}/add"


def _workspace_tool_provider_builtin_credential_info_path(provider_path):
    """GET .../builtin/{provider_path}/credential/info"""
    p = provider_path.strip("/")
    return f"{_WORKSPACE_TOOL_PROVIDER_BUILTIN_BASE}/{p}/credential/info"


def _workspace_tool_provider_builtin_delete_path(provider_path):
    """POST .../builtin/{provider_path}/delete"""
    p = provider_path.strip("/")
    return f"{_WORKSPACE_TOOL_PROVIDER_BUILTIN_BASE}/{p}/delete"


def add_workspace_builtin_tool_credential(
    client, provider_path="langgenius/github/github", **payload
):
    """
    POST /console/api/workspaces/current/tool-provider/builtin/{provider_path}/add
    在工作空间中添加内置工具提供商的自定义凭据（如 GitHub）。
    provider_path 默认 langgenius/github/github。
    payload 示例: {"credentials": {"access_tokens": "..."}, "type": "api-key", "name": "giggle_github"}
    response 示例: {"result": "success"}
    """
    path = _workspace_tool_provider_builtin_add_path(provider_path)
    return client.post(path, json=payload)


def get_workspace_builtin_tool_credential_info(
    client, provider_path="langgenius/github/github"
):
    """
    GET /console/api/workspaces/current/tool-provider/builtin/{provider_path}/credential/info
    查询当前工作空间内置工具提供商的自定义凭据信息（如 GitHub）。
    provider_path 默认 langgenius/github/github。
    """
    path = _workspace_tool_provider_builtin_credential_info_path(provider_path)
    return client.get(path)


def delete_workspace_builtin_tool_credential(
    client, credential_id, provider_path="langgenius/github/github", **payload
):
    """
    POST /console/api/workspaces/current/tool-provider/builtin/{provider_path}/delete
    删除工作空间内置工具提供商的自定义凭据。
    provider_path 默认 langgenius/github/github。
    body 示例: {"credential_id": "uuid"}；也可通过 **payload 传入完整 body。
    response 示例: {"result": "success"}
    """
    if payload:
        body = payload
    else:
        body = {"credential_id": credential_id}
    path = _workspace_tool_provider_builtin_delete_path(provider_path)
    return client.post(path, json=body)


def _model_provider_credentials_path(provider_path):
    """provider_path 例如 langgenius/tongyi/tongyi（不含首尾斜杠）。"""
    p = provider_path.strip("/")
    return f"{_WORKSPACE_MODEL_PROVIDERS_BASE}/{p}/credentials"


def _model_provider_credentials_switch_path(provider_path):
    """POST .../model-providers/{provider_path}/credentials/switch"""
    return f"{_model_provider_credentials_path(provider_path)}/switch"


def add_workspace_model_provider_credential(client, provider_path="langgenius/tongyi/tongyi", **payload):
    """
    POST /console/api/workspaces/current/model-providers/{provider_path}/credentials
    创建当前工作空间内模型提供商的自定义凭据。
    provider_path 默认 langgenius/tongyi/tongyi。
    payload 示例:
        {
            "credentials": {
                "dashscope_api_key": "sk-...",
                "use_international_endpoint": "false",
            },
            "name": "auto_test",
        }
    response 示例: {"result": "success"}
    """
    path = _model_provider_credentials_path(provider_path)
    return client.post(path, json=payload)


def delete_workspace_model_provider_credential(
    client, credential_id, provider_path="langgenius/tongyi/tongyi", **payload
):
    """
    DELETE /console/api/workspaces/current/model-providers/{provider_path}/credentials
    删除当前工作空间内模型提供商的自定义凭据。
    provider_path 默认 langgenius/tongyi/tongyi。
    body 示例: {"credential_id": "uuid"}；也可通过 **payload 传入完整 body。
    """
    if payload:
        body = payload
    else:
        body = {"credential_id": credential_id}
    path = _model_provider_credentials_path(provider_path)
    return client.delete(path, json=body)


def switch_workspace_model_provider_credential(
    client, credential_id, provider_path="langgenius/tongyi/tongyi", **payload
):
    """
    POST /console/api/workspaces/current/model-providers/{provider_path}/credentials/switch
    切换当前工作空间下该模型提供商正在使用的自定义凭据。
    provider_path 默认 langgenius/tongyi/tongyi。
    body 示例: {"credential_id": "uuid"}；也可通过 **payload 传入完整 body。
    response 示例: {"result": "success"}
    """
    if payload:
        body = payload
    else:
        body = {"credential_id": credential_id}
    path = _model_provider_credentials_switch_path(provider_path)
    return client.post(path, json=body)


def get_workspace_model_providers(client):
    """
    GET /console/api/workspaces/current/model-providers
    查询当前工作空间下模型提供商列表及详情（label、schema、custom_configuration 等）。
    无 request body。
    response 示例: {"data": [{"tenant_id": "...", "provider": "langgenius/tongyi/tongyi", ...}, ...]}
    """
    return client.get(_WORKSPACE_MODEL_PROVIDERS_BASE)
