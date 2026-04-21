from api.plugin_api import (
    apply_plugin,
    cleanup_plugin_install_task,
    delete_install_task,
    find_install_task_status_by_id,
    get_plugin_install_task_logs,
    get_plugin_settings,
    get_plugin_types,
    install_plugin,
    list_plugin_ids,
    list_plugin_install_tasks,
    list_plugins,
    put_plugin_settings,
    uninstall_plugin,
)
from services.base_service import BaseService
from utils.polling import wait_until


# 默认插件 payload
# 格式：plugin_name:version@runtime_hash，例如 langgenius/github:0.3.1@d11d1199e999...
DEFAULT_PLUGIN_PAYLOAD = {
    "plugin_id": "langgenius/github:0.3.1@d11d1199e99933a27fc210a3cb5579addb51a97e80b9f26dfb165eac6a6eadf5",
}

# 默认卸载插件 payload（PluginSimpleRequest，使用 pluginUniqueIdentifier）
DEFAULT_UNINSTALL_PLUGIN_PAYLOAD = {
    "pluginUniqueIdentifier": "langgenius/github:0.3.1@d11d1199e99933a27fc210a3cb5579addb51a97e80b9f26dfb165eac6a6eadf5",
}

# 插件安装范围（Dashboard PUT /plugin/settings 示例）
PLUGIN_INSTALLATION_SCOPE_OFFICIAL_ONLY = "PLUGIN_INSTALLATION_SCOPE_OFFICIAL_ONLY"
DEFAULT_PLUGIN_SETTINGS_PAYLOAD = {
    "pluginInstallationScope": PLUGIN_INSTALLATION_SCOPE_OFFICIAL_ONLY,
    "restrictToMarketplaceOnly": False,
}

# GET /plugin-manager/plugins/types/{plugin_id} 默认查询的插件 ID
DEFAULT_PLUGIN_TYPE_PLUGIN_ID = "langgenius/tongyi"


class PluginService(BaseService):

    def install_plugin_success(self, client=None, **overrides):
        """
        安装插件成功：POST /v1/plugin-manager/plugins/install，断言 200，返回响应体。
        若传入 client 则使用该 client（如 fixture admin_client），否则内部 admin_login()。
        overrides 会覆盖默认 payload，例如 plugin_id="other/plugin:1.0.0@hash"。
        """
        client = self.get_admin_client(client)
        payload = {**DEFAULT_PLUGIN_PAYLOAD, **overrides}
        res = install_plugin(client, **payload)
        data = self.assert_and_parse(res, message="安装插件失败")
        # 兼容 API 返回 taskIds 列表：规范为单一 task_id 便于调用方使用
        if isinstance(data.get("taskIds"), list) and data["taskIds"]:
            data["task_id"] = data["taskIds"][0]
        return data

    def uninstall_plugin_success(self, client=None, **overrides):
        """
        卸载插件成功：POST /v1/plugin-manager/plugins/uninstall，断言 200。
        若传入 client 则使用该 client（如 fixture admin_client），否则内部 admin_login()。
        overrides 会覆盖默认 payload，例如 pluginUniqueIdentifier="other/plugin:1.0.0@hash"。
        """
        client = self.get_admin_client(client)
        payload = {**DEFAULT_UNINSTALL_PLUGIN_PAYLOAD, **overrides}
        res = uninstall_plugin(client, **payload)
        return self.assert_and_parse(res, message="卸载插件失败")

    def list_install_task_results(self, client=None, page_number=1, results_per_page=100):
        """
        查询安装任务结果：GET /v1/plugin-manager/install-tasks?pageNumber=1&resultsPerPage=100，
        断言 200，返回 ListInstallTasksReply 响应体（含任务列表及状态）。
        """
        client = self.get_admin_client(client)
        res = list_plugin_install_tasks(
            client,
            page_number=page_number,
            results_per_page=results_per_page,
        )
        data = self.assert_and_parse(res, message="查询安装任务失败")
        assert isinstance(data.get("data") or [], list), f"安装任务列表响应格式异常: {data}"
        return data

    def list_plugins_success(
        self,
        client=None,
        category=None,
        keyword=None,
        page_number=None,
        results_per_page=None,
    ):
        client = self.get_admin_client(client)
        res = list_plugins(
            client,
            category=category,
            keyword=keyword,
            page_number=page_number,
            results_per_page=results_per_page,
        )
        data = self.assert_and_parse(res, message="查询插件列表失败")
        assert isinstance(data.get("data") or [], list), f"插件列表响应格式异常: {data}"
        return data

    def list_plugin_ids_success(
        self,
        client=None,
        category=None,
        keyword=None,
        page_number=1,
        results_per_page=10,
    ):
        client = self.get_admin_client(client)
        res = list_plugin_ids(
            client,
            category=category,
            keyword=keyword,
            page_number=page_number,
            results_per_page=results_per_page,
        )
        data = self.assert_and_parse(res, message="查询插件 ID 列表失败")
        assert isinstance(data.get("data") or [], list), f"插件 ID 列表响应格式异常: {data}"
        return data

    def get_install_task_logs_success(self, task_id, client=None):
        client = self.get_admin_client(client)
        res = get_plugin_install_task_logs(client, task_id)
        return self.assert_and_parse(res, message="查询安装任务日志失败")

    def delete_install_task_success(self, task_id, client=None):
        client = self.get_admin_client(client)
        res = delete_install_task(client, task_id)
        return self.assert_and_parse(res, message="删除安装任务失败")

    def cleanup_install_tasks_success(self, client=None):
        client = self.get_admin_client(client)
        res = cleanup_plugin_install_task(client)
        return self.assert_and_parse(res, message="清理安装任务失败")

    def wait_for_install_task_success(
        self,
        task_id,
        client=None,
        timeout=60,
        interval=3,
        success_statuses=("success", "completed", "succeeded"),
        failed_statuses=("failed", "error"),
    ):
        client = self.get_admin_client(client)

        def get_task_status():
            list_body = self.list_install_task_results(
                client=client,
                page_number=1,
                results_per_page=100,
            )
            status = find_install_task_status_by_id(list_body, task_id)
            if status and status.lower() in {s.lower() for s in failed_statuses}:
                raise AssertionError(f"安装任务失败, taskId={task_id}, status={status}")
            return status

        return wait_until(
            get_task_status,
            timeout=timeout,
            interval=interval,
            success_condition=lambda s: s and s.lower() in {x.lower() for x in success_statuses},
        )

    def apply_plugin_success(self, client=None, **payload):
        client = self.get_admin_client(client)
        res = apply_plugin(client, **payload)
        return self.assert_and_parse(res, message="分配插件失败")

    def get_plugin_types_success(self, client=None, plugin_id=None):
        """
        GET /v1/plugin-manager/plugins/types/{plugin_id}，断言 200。
        未传 ``plugin_id`` 时使用 ``DEFAULT_PLUGIN_TYPE_PLUGIN_ID``（默认 ``langgenius/tongyi``）。
        校验响应含 ``pluginId``、``plugins`` 列表。
        """
        client = self.get_admin_client(client)
        pid = plugin_id if plugin_id is not None else DEFAULT_PLUGIN_TYPE_PLUGIN_ID
        res = get_plugin_types(client, pid)
        data = self.assert_and_parse(res, message="查询插件类型版本失败")
        assert isinstance(data, dict), f"插件类型响应格式异常: {data}"
        assert data.get("pluginId") == pid, (
            f"响应 pluginId 应与请求一致: 期望 {pid!r}, 实际 {data.get('pluginId')!r}"
        )
        assert isinstance(data.get("plugins") or [], list), (
            f"响应 plugins 应为列表: {data}"
        )
        return data

    def get_plugin_settings_success(self, client=None):
        """
        GET /v1/dashboard/api/plugin/settings，断言 200，返回设置体
        （含 ``pluginInstallationScope``、``restrictToMarketplaceOnly``）。
        """
        client = self.get_admin_client(client)
        res = get_plugin_settings(client)
        data = self.assert_and_parse(res, message="查询插件设置失败")
        assert isinstance(data, dict), f"插件设置响应格式异常: {data}"
        return data

    def put_plugin_settings_success(self, client=None, **payload):
        """
        PUT /v1/dashboard/api/plugin/settings，断言 200，返回更新后的设置体。
        未传字段时默认使用 ``DEFAULT_PLUGIN_SETTINGS_PAYLOAD``。
        """
        client = self.get_admin_client(client)
        body = {**DEFAULT_PLUGIN_SETTINGS_PAYLOAD, **payload}
        res = put_plugin_settings(client, **body)
        data = self.assert_and_parse(res, message="更新插件设置失败")
        assert isinstance(data, dict), f"插件设置响应格式异常: {data}"
        return data
