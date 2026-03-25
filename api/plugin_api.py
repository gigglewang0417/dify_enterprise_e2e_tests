from urllib.parse import urlencode

from common.config import config

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
    从 list_plugin_ids 的 response.data 中按 pluginId 找到对应项，再按 pluginUniqueIdentifier 在 plugins 中筛选出唯一插件。
    找到返回该插件 dict，否则返回 None。
    """
    if not list_ids_data or not plugin_id or not plugin_unique_identifier:
        return None
    for item in list_ids_data:
        if item.get("pluginId") != plugin_id:
            continue
        for p in item.get("plugins") or []:
            if p.get("pluginUniqueIdentifier") == plugin_unique_identifier:
                return p
    return None


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
