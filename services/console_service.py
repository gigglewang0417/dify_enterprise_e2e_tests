from api.console_api import (
    add_workspace_builtin_tool_credential,
    add_workspace_model_provider_credential,
    get_workspace_builtin_tool_credential_info,
    get_workspace_model_providers,
    install_workspace_plugins_from_marketplace,
    list_workspace_plugin_installations_ids,
    list_workspace_plugin_latest_versions,
    switch_workspace_model_provider_credential,
)
from services.base_service import BaseService

# 默认：从应用市场安装的插件唯一标识列表（可覆盖）
DEFAULT_MARKETPLACE_PLUGIN_UNIQUE_IDENTIFIERS = [
    "jayfish0/agentql:1.0.0@03d116b2eb1d959af6d01d6389c7e5e34b3714d50c4cce058ea456dce94e2efa",
]


class ConsoleService(BaseService):

    def add_workspace_builtin_tool_credential_success(
        self,
        client=None,
        provider_path="langgenius/github/github",
        expected_status=200,
        **payload,
    ):
        client = self.get_console_client(client)
        res = add_workspace_builtin_tool_credential(client, provider_path=provider_path, **payload)
        data = self.assert_and_parse(res, expected_status=expected_status, message="添加工作空间内置工具凭据失败")
        result = data.get("result")
        assert result in (None, "success"), f"添加工作空间内置工具凭据结果异常: {data}"
        return data

    def get_workspace_builtin_tool_credential_info_success(
        self,
        client=None,
        provider_path="langgenius/github/github",
    ):
        client = self.get_console_client(client)
        res = get_workspace_builtin_tool_credential_info(client, provider_path=provider_path)
        data = self.assert_and_parse(res, message="查询工作空间内置工具凭据失败")
        assert isinstance(data.get("credentials") or [], list), f"工作空间内置工具凭据响应格式异常: {data}"
        return data

    def add_workspace_model_provider_credential_success(
        self,
        client=None,
        provider_path="langgenius/tongyi/tongyi",
        expected_status=201,
        **payload,
    ):
        client = self.get_console_client(client)
        res = add_workspace_model_provider_credential(client, provider_path=provider_path, **payload)
        data = self.assert_and_parse(res, expected_status=expected_status, message="添加工作空间模型凭据失败")
        result = data.get("result")
        assert result in (None, "success"), f"添加工作空间模型凭据结果异常: {data}"
        return data

    def switch_workspace_model_provider_credential_success(
        self,
        credential_id,
        client=None,
        provider_path="langgenius/tongyi/tongyi",
        **payload,
    ):
        client = self.get_console_client(client)
        res = switch_workspace_model_provider_credential(
            client,
            credential_id,
            provider_path=provider_path,
            **payload,
        )
        data = self.assert_and_parse(res, message="切换工作空间模型凭据失败")
        result = data.get("result")
        assert result in (None, "success"), f"切换工作空间模型凭据结果异常: {data}"
        return data

    def get_workspace_model_providers_success(self, client=None):
        client = self.get_console_client(client)
        res = get_workspace_model_providers(client)
        data = self.assert_and_parse(res, message="查询工作空间模型提供商失败")
        assert isinstance(data.get("data") or [], list), f"工作空间模型提供商响应格式异常: {data}"
        return data

    def install_workspace_plugins_from_marketplace_success(
        self,
        client=None,
        plugin_unique_identifiers=None,
        **payload,
    ):
        client = self.get_console_client(client)
        body = dict(payload)
        if plugin_unique_identifiers is not None:
            if isinstance(plugin_unique_identifiers, str):
                body["plugin_unique_identifiers"] = [plugin_unique_identifiers]
            else:
                body["plugin_unique_identifiers"] = list(plugin_unique_identifiers)
        elif "plugin_unique_identifiers" not in body:
            body["plugin_unique_identifiers"] = list(DEFAULT_MARKETPLACE_PLUGIN_UNIQUE_IDENTIFIERS)
        else:
            ids = body["plugin_unique_identifiers"]
            if isinstance(ids, str):
                body["plugin_unique_identifiers"] = [ids]
        res = install_workspace_plugins_from_marketplace(client, **body)
        data = self.assert_and_parse(res, message="从应用市场安装插件失败")
        assert isinstance(data, dict), f"应用市场安装插件响应格式异常: {data}"
        assert "all_installed" in data, f"响应中缺少 all_installed: {data}"
        return data

    def list_workspace_plugin_latest_versions_success(
        self,
        client=None,
        plugin_ids=None,
        **payload,
    ):
        client = self.get_console_client(client)
        body = dict(payload)
        if plugin_ids is not None:
            if isinstance(plugin_ids, str):
                body["plugin_ids"] = [plugin_ids]
            else:
                body["plugin_ids"] = list(plugin_ids)
        elif "plugin_ids" not in body:
            body["plugin_ids"] = ["langgenius/gemini", "langgenius/tongyi"]
        else:
            ids = body["plugin_ids"]
            if isinstance(ids, str):
                body["plugin_ids"] = [ids]
        res = list_workspace_plugin_latest_versions(client, **body)
        data = self.assert_and_parse(res, message="查询插件最新版本失败")
        assert isinstance(data.get("versions"), dict), f"响应中缺少 versions 或格式异常: {data}"
        return data

    def list_workspace_plugin_installations_ids_success(
        self,
        client=None,
        plugin_ids=None,
        **payload,
    ):
        client = self.get_console_client(client)
        body = dict(payload)
        if plugin_ids is not None:
            if isinstance(plugin_ids, str):
                body["plugin_ids"] = [plugin_ids]
            else:
                body["plugin_ids"] = list(plugin_ids)
        elif "plugin_ids" not in body:
            body["plugin_ids"] = ["langgenius/tongyi", "langgenius/gemini"]
        else:
            ids = body["plugin_ids"]
            if isinstance(ids, str):
                body["plugin_ids"] = [ids]
        res = list_workspace_plugin_installations_ids(client, **body)
        data = self.assert_and_parse(res, message="查询插件安装实例失败")
        assert isinstance(data.get("plugins"), list), f"响应中缺少 plugins 或格式异常: {data}"
        return data
