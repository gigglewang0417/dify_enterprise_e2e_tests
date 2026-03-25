from api.admin_user import (
    create_user,
    delete_user,
    get_user,
    list_users,
    reset_user_password,
    update_user,
)
from services.base_service import BaseService


class UserService(BaseService):

    def create_user_success(self, email, name, status='active', client=None):
        """创建系统用户成功：POST /v1/dashboard/api/users，断言 200，返回响应体（含 id、user 等）。
        若传入 client 则使用该 client（如 fixture admin_client），否则内部 admin_login()。
        """
        client = self.get_admin_client(client)
        payload = {"email": email, "name": name or email, "status": status}
        res = create_user(client, **payload)
        data = self.assert_and_parse(res, message="创建系统用户失败")
        user_id = data.get("id") or (data.get("user") or {}).get("id")
        assert user_id, f"响应中缺少 id: {data}"
        return data

    def delete_user_success(self, user_id, client=None):
        """删除系统用户成功：DELETE /v1/dashboard/api/users/{id}，断言 200，响应体为空或空 JSON 则视为成功。"""
        client = self.get_admin_client(client)
        res = delete_user(client, user_id)
        self.assert_status_code(res, message="删除系统用户失败")
        return self.parse_json(res)

    def list_users_success(
        self,
        client=None,
        email=None,
        status=None,
        page_number=None,
        results_per_page=None,
        reverse=None,
    ):
        client = self.get_admin_client(client)
        res = list_users(
            client,
            email=email,
            status=status,
            page_number=page_number,
            results_per_page=results_per_page,
            reverse=reverse,
        )
        data = self.assert_and_parse(res, message="查询系统用户列表失败")
        assert isinstance(data.get("data") or [], list), f"系统用户列表响应格式异常: {data}"
        return data

    def get_user_success(self, user_id, client=None):
        client = self.get_admin_client(client)
        res = get_user(client, user_id)
        data = self.assert_and_parse(res, message="查询系统用户详情失败")
        returned_id = data.get("id") or (data.get("user") or {}).get("id")
        assert returned_id == user_id, f"系统用户详情返回的 id 与请求不一致: {data}"
        return data

    def update_user_success(self, user_id, client=None, **payload):
        client = self.get_admin_client(client)
        res = update_user(client, user_id, **payload)
        data = self.assert_and_parse(res, message="更新系统用户失败")
        returned_id = data.get("id") or (data.get("user") or {}).get("id") or user_id
        assert returned_id == user_id, f"更新系统用户返回的 id 与请求不一致: {data}"
        return data

    def reset_user_password_success(self, user_id, client=None, **payload):
        client = self.get_admin_client(client)
        res = reset_user_password(client, user_id, **payload)
        return self.assert_and_parse(res, message="重置系统用户密码失败")
