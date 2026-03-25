from api.member_api import (
    create_member,
    delete_member,
    get_member,
    list_members,
    reset_member_password,
    update_member,
)
from services.base_service import BaseService


class MemberService(BaseService):

    def create_member_response(self, email, name, status="active", client=None):
        client = self.get_admin_client(client)
        payload = {"email": email, "name": name, "status": status}
        return create_member(client, **payload)

    def create_member_success(self, email, name, status='active', client=None):
        """创建成员成功：POST /v1/dashboard/api/members，断言 200，返回响应体（含 id、password 等）。
        若传入 client 则使用该 client（如 fixture admin_client），否则内部 admin_login()。
        """
        client = self.get_admin_client(client)
        payload = {"email": email, "name": name, "status": status}
        res = create_member(client, **payload)
        data = self.assert_and_parse(res, message="创建成员失败")
        # 支持顶层 id/password 或 data.member
        member_id = data.get("id") or (data.get("member") or {}).get("id")
        assert member_id, f"响应中缺少 id: {data}"
        return data

    def delete_member_success(self, member_id, client=None):
        """删除成员成功：DELETE /v1/dashboard/api/members/{id}，断言 200，响应体为空或空 JSON 则视为成功。"""
        client = self.get_admin_client(client)
        res = delete_member(client, member_id)
        self.assert_status_code(res, message="删除成员失败")
        return self.parse_json(res)

    def list_members_success(
        self,
        client=None,
        email=None,
        status=None,
        workspace_id=None,
        page_number=1,
        results_per_page=10,
        reverse=True,
        group_name=None,
    ):
        client = self.get_admin_client(client)
        res = list_members(
            client,
            email=email,
            status=status,
            workspace_id=workspace_id,
            page_number=page_number,
            results_per_page=results_per_page,
            reverse=reverse,
            group_name=group_name,
        )
        data = self.assert_and_parse(res, message="查询成员列表失败")
        assert isinstance(data.get("data") or [], list), f"成员列表响应格式异常: {data}"
        return data

    def get_member_success(self, member_id, client=None):
        client = self.get_admin_client(client)
        res = get_member(client, member_id)
        data = self.assert_and_parse(res, message="查询成员详情失败")
        returned_id = data.get("id") or (data.get("member") or {}).get("id")
        assert returned_id == member_id, f"成员详情返回的 id 与请求不一致: {data}"
        return data

    def update_member_success(self, member_id, client=None, **payload):
        client = self.get_admin_client(client)
        res = update_member(client, member_id, **payload)
        data = self.assert_and_parse(res, message="更新成员失败")
        returned_id = data.get("id") or (data.get("member") or {}).get("id") or member_id
        assert returned_id == member_id, f"更新成员返回的 id 与请求不一致: {data}"
        return data

    def update_member_response(self, member_id, client=None, **payload):
        client = self.get_admin_client(client)
        return update_member(client, member_id, **payload)

    def reset_member_password_success(self, member_id, client=None, **payload):
        client = self.get_admin_client(client)
        res = reset_member_password(client, member_id, **payload)
        return self.assert_and_parse(res, message="重置成员密码失败")

    def reset_member_password_response(self, member_id, client=None, **payload):
        client = self.get_admin_client(client)
        return reset_member_password(client, member_id, **payload)
