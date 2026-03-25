from api.admin_secret_key import create_secret_key, delete_secret_key, list_secret_keys
from services.base_service import BaseService


# 默认创建密钥 payload（CreateSecretKeyReq）
DEFAULT_CREATE_SECRET_KEY_PAYLOAD = {
    "name": "auto_test",
}


class SecretKeyService(BaseService):

    def create_secret_key_success(self, client=None, **overrides):
        """
        新增密钥
        """
        client = self.get_admin_client(client)
        payload = {**DEFAULT_CREATE_SECRET_KEY_PAYLOAD, **overrides}
        res = create_secret_key(client, **payload)
        data = self.assert_and_parse(res, message="新增密钥失败")
        secret_key_id = data.get("id")
        assert secret_key_id, f"新增密钥响应中缺少 id: {data}"
        return data

    def delete_secret_key_success(self, secret_key_id, client=None):
        """
        删除密钥成功：DELETE /v1/dashboard/api/admin-secret-keys/{id}，断言 200。
        响应示例：{"message": "Secret key deleted successfully"}
        """
        client = self.get_admin_client(client)
        res = delete_secret_key(client, secret_key_id)
        data = self.assert_and_parse(res, message="删除密钥失败")
        assert data.get("message"), f"删除密钥响应缺少 message: {data}"
        return data

    def list_secret_keys_success(self, client=None, status=None, page_number=None, results_per_page=None, reverse=None):
        client = self.get_admin_client(client)
        res = list_secret_keys(
            client,
            status=status,
            page_number=page_number,
            results_per_page=results_per_page,
            reverse=reverse,
        )
        data = self.assert_and_parse(res, message="查询密钥列表失败")
        assert isinstance(data.get("data") or [], list), f"密钥列表响应格式异常: {data}"
        return data
