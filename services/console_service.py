from api.console_api import (
    add_workspace_builtin_tool_credential,
    add_workspace_model_provider_credential,
    get_workspace_builtin_tool_credential_info,
    get_workspace_model_providers,
    switch_workspace_model_provider_credential,
)
from services.base_service import BaseService


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
