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

# 当前工作空间成员：邮箱邀请
_WORKSPACE_MEMBERS_INVITE_EMAIL_PATH = (
    f"{_CONSOLE_API_BASE}/workspaces/current/members/invite-email"
)

# 当前工作空间：从应用市场安装插件
_WORKSPACE_PLUGIN_INSTALL_MARKETPLACE_PATH = (
    f"{_CONSOLE_API_BASE}/workspaces/current/plugin/install/marketplace"
)

# 当前工作空间：批量查询插件最新版本
_WORKSPACE_PLUGIN_LIST_LATEST_VERSIONS_PATH = (
    f"{_CONSOLE_API_BASE}/workspaces/current/plugin/list/latest-versions"
)

# 当前工作空间：按插件 ID 批量查询已安装实例（installations）
_WORKSPACE_PLUGIN_LIST_INSTALLATIONS_IDS_PATH = (
    f"{_CONSOLE_API_BASE}/workspaces/current/plugin/list/installations/ids"
)


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


def add_workspace_model_provider_credential(client, provider_path="langgenius/tongyi", **payload):
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


def invite_workspace_members_by_email(
    client,
    emails,
    role="normal",
    language="zh-Hans",
    **payload,
):
    if payload:
        body = payload
    else:
        email_list = emails if isinstance(emails, list) else [emails]
        body = {"emails": email_list, "role": role, "language": language}
    return client.post(_WORKSPACE_MEMBERS_INVITE_EMAIL_PATH, json=body)


def install_workspace_plugins_from_marketplace(client, **payload):
    """
    POST /console/api/workspaces/current/plugin/install/marketplace
    从应用市场按插件唯一标识安装到当前工作空间。

    requestBody 示例::
        {"plugin_unique_identifiers": ["jayfish0/agentql:1.0.0@03d116b2eb1d..."]}

    response 示例::
        {"all_installed": true, "task_id": ""}
    """
    return client.post(_WORKSPACE_PLUGIN_INSTALL_MARKETPLACE_PATH, json=payload)


def list_workspace_plugin_latest_versions(client, **payload):
    """
    POST /console/api/workspaces/current/plugin/list/latest-versions
    批量查询指定插件 ID 在当前工作空间下的最新版本信息。
    """
    return client.post(_WORKSPACE_PLUGIN_LIST_LATEST_VERSIONS_PATH, json=payload)


def list_workspace_plugin_installations_ids(client, **payload):
    """
    POST /console/api/workspaces/current/plugin/list/installations/ids
    按 plugin_ids 批量查询当前工作空间内已安装的插件实例列表。

    requestBody 示例::
        {"plugin_ids": ["langgenius/tongyi", "langgenius/gemini"]}

    response 示例::
        {"plugins": [{"id": "...", "tenant_id": "...", "plugin_id": "langgenius/tongyi",
          "plugin_unique_identifier": "langgenius/tongyi:0.1.34@...", "version": "0.1.34",
          "declaration": {...}, ...}, ...]}
    """
    return client.post(_WORKSPACE_PLUGIN_LIST_INSTALLATIONS_IDS_PATH, json=payload)

