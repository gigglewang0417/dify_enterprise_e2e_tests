from urllib.parse import urlencode

from common.config import config

# 企业后台 Dashboard API（与 workspace_api 中 _DASHBOARD_API_BASE 一致）
_DASHBOARD_API_BASE = f"{config.base_url}/dashboard/api"
PLUGIN_SETTINGS_PATH = f"{_DASHBOARD_API_BASE}/plugin/settings"

# 路径常量（与 OpenAPI PluginManagerPlugin 一致）
PLUGINS_BASE_PATH = f"{config.base_url}/plugin-manager/plugins"
PLUGINS_APPLY_PATH = f"{config.base_url}/plugin-manager/plugins/apply"
PLUGINS_IDS_PATH = f"{config.base_url}/plugin-manager/plugins/ids"
PLUGINS_INSTALL_PATH = f"{config.base_url}/plugin-manager/plugins/install"
PLUGINS_UNINSTALL_PATH = f"{config.base_url}/plugin-manager/plugins/uninstall"

# PluginInstallTask
INSTALL_TASKS_BASE_PATH = f"{config.base_url}/plugin-manager/install-tasks"
INSTALL_TASKS_CLEANUP_PATH = f"{config.base_url}/plugin-manager/install-tasks/cleanup"


def _install_task_by_id_path(task_id):
    return f"{INSTALL_TASKS_BASE_PATH}/{task_id}"


def _plugin_types_by_plugin_id_path(plugin_id):
    """
    ``GET .../plugins/types/{plugin_id}``，``plugin_id`` 如 ``langgenius/tongyi``（可含 ``/``）。
    """
    pid = (plugin_id or "").strip().strip("/")
    return f"{PLUGINS_BASE_PATH}/types/{pid}"


def _plugin_ids_path(category=None, keyword=None, page_number=1, results_per_page=10):
    """拼接 GET /v1/plugin-manager/plugins/ids 的 path（含 query 参数），例如 .../plugins/ids?keyword=github&pageNumber=1&resultsPerPage=10。"""
    params = {
        "pageNumber": page_number,
        "resultsPerPage": results_per_page,
    }
    if category is not None:
        params["category"] = category
    if keyword is not None:
        params["keyword"] = keyword
    return f"{PLUGINS_IDS_PATH}?{urlencode(params)}"


def list_plugins(
    client,
    category=None,
    keyword=None,
    page_number=None,
    results_per_page=None,
):
    """
    GET /v1/plugin-manager/plugins
    PluginManagerPlugin_ListPlugins - List installed plugins
    query: category, keyword, pageNumber, resultsPerPage
    response: ListPluginsReply
    """
    params = {}
    if category is not None:
        params["category"] = category
    if keyword is not None:
        params["keyword"] = keyword
    if page_number is not None:
        params["pageNumber"] = page_number
    if results_per_page is not None:
        params["resultsPerPage"] = results_per_page
    return client.get(PLUGINS_BASE_PATH, params=params if params else None)


def apply_plugin(client, **payload):
    """
    POST /v1/plugin-manager/plugins/apply
    PluginManagerPlugin_ApplyPlugin - Apply plugin to tenants.
    If the plugin is already installed with an older version, it will be upgraded to the latest version.
    Plugins will be uninstalled from tenants that already installed the plugin but is not declared in the request.
    requestBody: ApplyPluginRequest (required)
    response: ApplyPluginReply
    """
    return client.post(PLUGINS_APPLY_PATH, json=payload)


def get_plugin_types(client, plugin_id):
    """
    GET /v1/plugin-manager/plugins/types/{plugin_id}
    按插件 ID（如 ``langgenius/tongyi``）查询分类、各版本 ``pluginUniqueIdentifier``、安装租户等。

    response 含 ``pluginId``、``category``、``plugins``（版本列表，每项含 ``version``、
    ``pluginUniqueIdentifier``、``installations`` 等）。
    """
    path = _plugin_types_by_plugin_id_path(plugin_id)
    return client.get(path)


def list_plugin_ids(
    client,
    category=None,
    keyword=None,
    page_number=1,
    results_per_page=10,
):
    """
    GET /v1/plugin-manager/plugins/ids
    PluginManagerPlugin_ListPluginIds - List installed plugin ids (each id may have multiple versions)
    query: category, keyword, pageNumber(默认1), resultsPerPage(默认10)
    response: ListPluginIdsReply
    """
    path = _plugin_ids_path(category=category, keyword=keyword, page_number=page_number, results_per_page=results_per_page)
    return client.get(path)


def find_plugin_by_ids(list_ids_data, plugin_id, plugin_unique_identifier):
    """
    从 ``list_plugin_ids`` 的 ``response.data`` 中**先按 pluginId 定位到条目，再按
    pluginUniqueIdentifier 精确过滤到目标版本**的子项（``plugins`` 列表里同一个 ``pluginId`` 下
    可能并存多个版本，每个版本有各自独立的 ``installations``）。

    匹配规则：
    1. 外层按 ``pluginId == plugin_id`` 定位到一个或多个条目；
    2. 内层按 ``pluginUniqueIdentifier == plugin_unique_identifier`` 精确过滤到具体版本；
    3. 若用户传入的 ``plugin_unique_identifier`` 不含 ``@checksum``（形如 ``name:version``），
       回退按 ``<plugin_id>:<version>`` 前缀匹配，用于宽松场景。
    命中返回该版本 dict；未命中返回 ``None``。
    """
    if not list_ids_data or not plugin_id or not plugin_unique_identifier:
        return None
    fallback_prefix = (
        plugin_unique_identifier
        if "@" in plugin_unique_identifier
        else f"{plugin_unique_identifier}@"
    )
    loose_match = None
    for item in list_ids_data:
        if item.get("pluginId") != plugin_id:
            continue
        for p in item.get("plugins") or []:
            uid = p.get("pluginUniqueIdentifier") or ""
            if uid == plugin_unique_identifier:
                return p
            if loose_match is None and uid.startswith(fallback_prefix):
                loose_match = p
    return loose_match


def extract_installed_tenant_ids(plugin_version_entry):
    """
    从**单条插件版本条目**（即 ``find_plugin_by_ids`` 的返回值，或 ``get_plugin_types`` 中
    ``plugins[*]``）的 ``installations`` 字段中提取已安装租户 ID 列表。

    注意：``installations`` 是**版本级**字段——同一个 ``pluginId`` 的不同版本各自维护独立
    的租户列表，调用方需先把目标版本的条目传入，本函数不做跨版本聚合。

    兼容三种常见形态：
    - ``installations: ["<tenantId>", ...]``
    - ``installations: [{"tenantId": "...", "source": "..."}, ...]``（当前服务端形态）
    - ``installations: [{"tenant_id": "..."}, ...]``
    未匹配到时返回空列表。
    """
    if not isinstance(plugin_version_entry, dict):
        return []
    installations = plugin_version_entry.get("installations") or []
    tenant_ids = []
    for item in installations:
        if isinstance(item, str):
            tid = item.strip()
        elif isinstance(item, dict):
            tid = (
                item.get("tenantId")
                or item.get("tenant_id")
                or item.get("TenantId")
                or item.get("id")
            )
        else:
            tid = None
        if tid:
            tenant_ids.append(tid)
    return tenant_ids


def find_install_task_status_by_id(list_reply, task_id):
    """从 ListInstallTasksReply 中按 id 查找任务，返回 status，未找到返回 None。"""
    if not isinstance(list_reply, dict):
        return None
    for task in list_reply.get("data") or []:
        if isinstance(task, dict) and task.get("id") == task_id:
            return task.get("status")
    return None


def install_plugin(client, **payload):
    """
    POST /v1/plugin-manager/plugins/install
    PluginManagerPlugin_InstallPlugin - Install plugin runtime and allocate to tenants
    requestBody: InstallPluginRequest (required)
    response: InstallPluginReply
    """
    return client.post(PLUGINS_INSTALL_PATH, json=payload)


def uninstall_plugin(client, **payload):
    """
    POST /v1/plugin-manager/plugins/uninstall
    PluginManagerPlugin_UninstallPlugin - Uninstall plugin and runtime from all tenants
    requestBody: PluginSimpleRequest (required)
    response: 200, content: {}
    """
    return client.post(PLUGINS_UNINSTALL_PATH, json=payload)


def list_plugin_install_tasks(client, page_number=None, results_per_page=None):
    """
    GET /v1/plugin-manager/install-tasks
    PluginInstallTask_ListPluginInstallTasks
    query: pageNumber, resultsPerPage
    response: ListInstallTasksReply
    """
    params = {}
    if page_number is not None:
        params["pageNumber"] = page_number
    if results_per_page is not None:
        params["resultsPerPage"] = results_per_page
    return client.get(INSTALL_TASKS_BASE_PATH, params=params if params else None)


def cleanup_plugin_install_task(client):
    """
    DELETE /v1/plugin-manager/install-tasks/cleanup
    PluginInstallTask_CleanUpPluginInstallTask
    response: 200, content: {}
    """
    return client.delete(INSTALL_TASKS_CLEANUP_PATH)


def delete_install_task(client, task_id):
    """
    DELETE /v1/plugin-manager/install-tasks/{id}
    PluginInstallTask_DeleteInstallTask
    response: 200, content: {}
    """
    path = _install_task_by_id_path(task_id)
    return client.delete(path)


def get_plugin_install_task_logs(client, task_id):
    """
    GET /v1/plugin-manager/install-tasks/{id}/logs
    PluginInstallTask_GetPluginInstallTaskLogs
    response: GetInstallTaskLogsReply
    """
    path = f"{_install_task_by_id_path(task_id)}/logs"
    return client.get(path)


def get_plugin_settings(client):
    """
    GET /v1/dashboard/api/plugin/settings
    查询插件安装策略等设置。
    response 示例: ``{"pluginInstallationScope": "...", "restrictToMarketplaceOnly": bool}``
    """
    return client.get(PLUGIN_SETTINGS_PATH)


def put_plugin_settings(client, **payload):
    """
    PUT /v1/dashboard/api/plugin/settings
    更新插件安装策略等设置。
    requestBody 示例::
        {"pluginInstallationScope": "PLUGIN_INSTALLATION_SCOPE_OFFICIAL_ONLY", "restrictToMarketplaceOnly": false}
    """
    return client.put(PLUGIN_SETTINGS_PATH, json=payload)
