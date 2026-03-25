from services.auth_service import AuthService


class BaseService:

    @staticmethod
    def get_admin_client(client=None):
        if client is not None:
            return client
        client, _ = AuthService.admin_login()
        return client

    @staticmethod
    def get_console_client(client=None):
        if client is not None:
            return client
        client, _ = AuthService.console_login()
        return client

    @staticmethod
    def assert_status_code(response, expected_status=200, message="请求失败"):
        assert response.status_code == expected_status, (
            f"{message}: {response.status_code}, {response.text[:300]}"
        )
        return response

    @staticmethod
    def parse_json(response):
        return response.json() if getattr(response, "text", "") else {}

    @classmethod
    def assert_and_parse(cls, response, expected_status=200, message="请求失败"):
        cls.assert_status_code(response, expected_status=expected_status, message=message)
        return cls.parse_json(response)

    @staticmethod
    def require_field(data, field_name, message=None):
        value = data.get(field_name) if isinstance(data, dict) else None
        assert value is not None and value != "", message or f"响应中缺少字段 {field_name}: {data}"
        return value
