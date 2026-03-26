import copy
import os

from api.credentials_api import (
    check_credential_policy,
    create_credential,
    delete_credential,
    get_credential,
    get_credential_policy,
    list_credentials,
    list_credential_tenant_joins,
    operate_credential_tenant_joins,
    update_credential,
    update_credential_policy,
)
from services.base_service import BaseService


# 默认创建凭据 payload（CreateCredentialRequest）
DEFAULT_CREATE_CREDENTIAL_PAYLOAD = {
    "pluginId": "langgenius/github",
    "pluginName": "github",
    "pluginIcon": "b73c6560cb94e70396e2874a11da39d0bbb6263bb67bb2617d2d39226b04962b.svg",
    "pluginVersion": "0.3.2",
    "displayName": "giggle_1",
    "pluginArgs": {
        "access_tokens": os.getenv("TOOL_CREDENTIAL_KEY", "test-github-token")
    },
    "type": "CREDENTIAL_TYPE_PLUGIN",
}

# 默认分配凭据 payload（OperateCredentialTenantJoinsRequest）
DEFAULT_OPERATE_CREDENTIAL_TENANT_JOINS_PAYLOAD = {
    "isAll": False,
    "credentialId": "c56b9dde-686f-4f22-bde3-3830b28af2ae",
    "batchDeleteIds": [],
    "batchCreateCredentialTenantJoins": [
        {
            "displayName": "giggle_1",
            "allocatedTenant": "f0435a59-fc6b-4d40-a478-6a53d00bb922",
            "credentialId": "c56b9dde-686f-4f22-bde3-3830b28af2ae",
        }
    ],
}


class CredentialService(BaseService):

    def update_credential_response(self, credential_id, client=None, **payload):
        client = self.get_admin_client(client)
        return update_credential(client, credential_id, **payload)

    def create_credential_success(self, client=None, **overrides):
        """
        创建凭据成功：POST /v1/plugin-manager/credentials，断言 200，返回响应体。
        若传入 client 则使用该 client（如 fixture admin_client），否则内部 admin_login()。
        overrides 会覆盖默认 payload 中的字段，例如 displayName="my_cred", pluginArgs={...}。
        """
        client = self.get_admin_client(client)
        payload = copy.deepcopy(DEFAULT_CREATE_CREDENTIAL_PAYLOAD)
        payload.update(overrides)
        res = create_credential(client, **payload)
        data = self.assert_and_parse(res, message="创建凭据失败")
        credential_id = data.get("id") or (data.get("credential") or {}).get("id")
        assert credential_id, f"创建凭据响应中缺少 id: {data}"
        return data

    def operate_credential_tenant_joins_success(self, client=None, **overrides):
        """
        分配凭据成功：POST /v1/plugin-manager/credential-tenant-joins/operate，断言 200，返回响应体。
        若传入 client 则使用该 client（如 fixture admin_client），否则内部 admin_login()。
        overrides 会覆盖默认 payload 中的字段，例如 credentialId、batchCreateCredentialTenantJoins 等。
        """
        client = self.get_admin_client(client)
        payload = copy.deepcopy(DEFAULT_OPERATE_CREDENTIAL_TENANT_JOINS_PAYLOAD)
        payload.update(overrides)
        res = operate_credential_tenant_joins(client, **payload)
        return self.assert_and_parse(res, message="分配凭据失败")

    def delete_credential_success(self, credential_id, client=None):
        """
        删除凭据成功：POST /v1/plugin-manager/credentials/delete-with-usage-check，断言 200，返回响应体。
        payload 为 {"id": credential_id}，response 示例：{"items": []}。
        若传入 client 则使用该 client，否则内部 admin_login()。
        """
        client = self.get_admin_client(client)
        res = delete_credential(client, credential_id)
        return self.assert_and_parse(res, message="删除凭据失败")

    def list_credentials_success(
        self,
        client=None,
        search=None,
        credential_type=None,
        page_number=None,
        results_per_page=None,
        reverse=None,
    ):
        client = self.get_admin_client(client)
        res = list_credentials(
            client,
            search=search,
            credential_type=credential_type,
            page_number=page_number,
            results_per_page=results_per_page,
            reverse=reverse,
        )
        data = self.assert_and_parse(res, message="查询凭据列表失败")
        assert isinstance(data.get("data") or [], list), f"凭据列表响应格式异常: {data}"
        return data

    def get_credential_success(self, credential_id, client=None):
        client = self.get_admin_client(client)
        res = get_credential(client, credential_id)
        data = self.assert_and_parse(res, message="查询凭据详情失败")
        returned_id = data.get("id") or (data.get("credential") or {}).get("id")
        assert returned_id == credential_id, f"凭据详情返回的 id 与请求不一致: {data}"
        return data

    def update_credential_success(self, credential_id, client=None, **payload):
        client = self.get_admin_client(client)
        res = update_credential(client, credential_id, **payload)
        data = self.assert_and_parse(res, message="更新凭据失败")
        returned_id = data.get("id") or (data.get("credential") or {}).get("id") or credential_id
        assert returned_id == credential_id, f"更新凭据返回的 id 与请求不一致: {data}"
        return data

    def list_credential_tenant_joins_success(self, credential_id=None, client=None):
        client = self.get_admin_client(client)
        res = list_credential_tenant_joins(client, credential_id=credential_id)
        data = self.assert_and_parse(res, message="查询凭据分配关系失败")
        assert isinstance(data.get("data") or [], list), f"凭据分配关系响应格式异常: {data}"
        return data

    def get_credential_policy_success(self, client=None):
        client = self.get_admin_client(client)
        res = get_credential_policy(client)
        return self.assert_and_parse(res, message="查询凭据策略失败")

    def update_credential_policy_success(self, client=None, **payload):
        client = self.get_admin_client(client)
        res = update_credential_policy(client, **payload)
        return self.assert_and_parse(res, message="更新凭据策略失败")

    def update_credential_policy_response(self, client=None, **payload):
        client = self.get_admin_client(client)
        return update_credential_policy(client, **payload)

    def check_credential_policy_success(self, client=None, **payload):
        client = self.get_admin_client(client)
        res = check_credential_policy(client, **payload)
        return self.assert_and_parse(res, message="校验凭据策略失败")

    def check_credential_policy_response(self, client=None, **payload):
        client = self.get_admin_client(client)
        return check_credential_policy(client, **payload)
