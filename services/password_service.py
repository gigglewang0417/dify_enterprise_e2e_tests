from api.password_policy import (
    check_password_status,
    get_password_policy,
    get_password_strength,
    reset_password,
    update_password_policy,
)
from services.base_service import BaseService


# 默认修改密码策略 payload（PasswordPolicyConfig）
DEFAULT_UPDATE_PASSWORD_POLICY_PAYLOAD = {
    "minLength": 9,
    "requireDigit": True,
    "requireLowercase": True,
    "requireUppercase": False,
    "requireSpecial": False,
    "forbidRepeated": False,
    "forbidSequential": False,
    "expiryEnabled": False,
    "expiryDays": 1,
}


class PasswordService(BaseService):

    def reset_password_response(self, client=None, **payload):
        client = self.get_admin_client(client)
        return reset_password(client, **payload)

    def check_password_status_response(self, client=None):
        client = self.get_admin_client(client)
        return check_password_status(client)

    def update_password_policy_success(self, client=None, **overrides):
        """
        修改密码策略成功：PUT /v1/dashboard/api/password/policy，断言 200，返回响应体（PasswordPolicyConfig）。
        若传入 client 则使用该 client（如 fixture admin_client），否则内部 admin_login()。
        overrides 会覆盖默认 payload，例如 minLength=12、requireUppercase=True 等。
        """
        client = self.get_admin_client(client)
        payload = {**DEFAULT_UPDATE_PASSWORD_POLICY_PAYLOAD, **overrides}
        res = update_password_policy(client, **payload)
        return self.assert_and_parse(res, message="修改密码策略失败")

    def reset_password_success(self, client=None, **payload):
        """
        修改密码成功：POST /v1/dashboard/api/reset-password，断言 200，返回响应体。
        若传入 client 则使用该 client（当前登录用户修改自己的密码），否则内部 admin_login()。
        payload 需包含 currentPassword、newPassword、confirmPassword。
        """
        client = self.get_admin_client(client)
        res = reset_password(client, **payload)
        return self.assert_and_parse(res, message="修改密码失败")

    def get_password_policy_success(self, client=None):
        client = self.get_admin_client(client)
        res = get_password_policy(client)
        return self.assert_and_parse(res, message="查询密码策略失败")

    def check_password_status_success(self, client=None):
        client = self.get_admin_client(client)
        res = check_password_status(client)
        data = self.assert_and_parse(res, message="查询密码状态失败")
        assert "requirePasswordChange" in data, f"密码状态响应缺少 requirePasswordChange: {data}"
        return data

    def get_password_strength_success(self, password, client=None, **payload):
        client = self.get_admin_client(client)
        body = {"password": password, **payload}
        res = get_password_strength(client, **body)
        return self.assert_and_parse(res, message="查询密码强度失败")
