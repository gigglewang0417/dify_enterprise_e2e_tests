from api.admin_api import list_workspaces


class AdminService:

    @staticmethod
    def list_workspaces_success(secret_key, base_url=None, name=None, status=None, page=1, limit=10):
        res = list_workspaces(
            secret_key,
            base_url=base_url,
            name=name,
            status=status,
            page=page,
            limit=limit,
        )
        assert res.status_code == 200, f"Admin API 获取工作空间失败: {res.status_code}, {res.text[:300]}"
        assert res.text and res.text.strip(), "Admin API 返回 body 为空"
        return res.json()
