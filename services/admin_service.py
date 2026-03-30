from api.admin_api import (
    add_group_member,
    add_workspace_member,
    create_group,
    create_member,
    create_workspace,
    delete_group,
    delete_group_member,
    delete_member,
    delete_workspace,
    delete_workspace_member,
    export_app_dsl,
    get_group,
    import_workspace_dsl,
    get_member,
    get_workspace_member,
    get_workspace,
    list_group_members,
    list_groups,
    list_members,
    list_workspace_members,
    list_workspaces,
    update_group,
    update_member,
    update_workspace,
    update_workspace_member,
)


class AdminService:

    @staticmethod
    def _workspace_id_from_create_reply(data):
        if not isinstance(data, dict):
            return None
        if data.get("id"):
            return data.get("id")
        w = data.get("workspace")
        if isinstance(w, dict) and w.get("id"):
            return w.get("id")
        return None

    @staticmethod
    def _workspace_dict_from_reply(data):
        if not isinstance(data, dict):
            return None
        w = data.get("workspace")
        if isinstance(w, dict) and w.get("id"):
            return w
        if data.get("id"):
            return data
        return None

    @staticmethod
    def _member_id_from_reply(data):
        if not isinstance(data, dict):
            return None
        if data.get("id"):
            return data.get("id")
        m = data.get("member")
        if isinstance(m, dict) and m.get("id"):
            return m.get("id")
        return None

    @staticmethod
    def _member_dict_from_reply(data):
        if not isinstance(data, dict):
            return None
        m = data.get("member")
        if isinstance(m, dict) and m.get("id"):
            return m
        if data.get("id"):
            return data
        return None

    @staticmethod
    def _workspace_member_member_id_from_reply(data):
        if not isinstance(data, dict):
            return None
        for key in ("member_id", "memberId"):
            if data.get(key):
                return data.get(key)
        m = data.get("member")
        if isinstance(m, dict) and m.get("id"):
            return m.get("id")
        if data.get("id"):
            return data.get("id")
        return None

    @staticmethod
    def _workspace_role_from_reply(data):
        if not isinstance(data, dict):
            return None
        for key in ("workspace_role", "workspaceRole"):
            if data.get(key) is not None:
                return data.get(key)
        m = data.get("member")
        if isinstance(m, dict):
            return m.get("workspace_role") or m.get("workspaceRole")
        return None

    @staticmethod
    def _group_id_from_reply(data):
        if not isinstance(data, dict):
            return None
        if data.get("id"):
            return data.get("id")
        g = data.get("group")
        if isinstance(g, dict) and g.get("id"):
            return g.get("id")
        return None

    @staticmethod
    def _group_dict_from_reply(data):
        if not isinstance(data, dict):
            return None
        g = data.get("group")
        if isinstance(g, dict) and g.get("id"):
            return g
        if data.get("id"):
            return data
        return None

    @staticmethod
    def create_workspace_success(secret_key, name, owner_email, base_url=None):
        """POST Admin API /workspaces，返回 200 与解析后的 JSON，且包含 workspace id。"""
        res = create_workspace(
            secret_key,
            name=name,
            owner_email=owner_email,
            base_url=base_url,
        )
        assert res.status_code == 200, (
            f"Admin API 创建工作空间失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        workspace_id = AdminService._workspace_id_from_create_reply(data)
        assert workspace_id, f"Admin API 创建 workspace 响应中未解析到 id: {data}"
        return data, workspace_id

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

    @staticmethod
    def get_workspace_success(secret_key, workspace_id, base_url=None):
        """GET Admin API /workspaces/{id}，返回 200 与解析后的 JSON，且 id 与请求一致。"""
        res = get_workspace(secret_key, workspace_id, base_url=base_url)
        assert res.status_code == 200, (
            f"Admin API 获取工作空间失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        resolved_id = AdminService._workspace_id_from_create_reply(data)
        assert resolved_id == workspace_id, (
            f"Admin API 工作空间详情 id 与请求不一致: 期望 {workspace_id}, 解析 {resolved_id}, body: {data}"
        )
        return data

    @staticmethod
    def update_workspace_success(secret_key, workspace_id, name, status, base_url=None):
        """PUT Admin API /workspaces/{id}，返回 200 且响应中 name、status 与请求一致。"""
        res = update_workspace(
            secret_key,
            workspace_id,
            name=name,
            status=status,
            base_url=base_url,
        )
        assert res.status_code == 200, (
            f"Admin API 修改工作空间失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        w = AdminService._workspace_dict_from_reply(data)
        assert w, f"Admin API 修改 workspace 响应中未解析到 workspace: {data}"
        assert w.get("id") == workspace_id, (
            f"Admin API 修改后 workspace.id 与请求不一致: {w}"
        )
        assert w.get("name") == name, f"Admin API 修改后 name 不符合预期: {w}"
        assert w.get("status") == status, f"Admin API 修改后 status 不符合预期: {w}"
        return data

    @staticmethod
    def delete_workspace_success(secret_key, workspace_id, base_url=None):
        """DELETE Admin API /workspaces/{id}，返回 200。"""
        res = delete_workspace(secret_key, workspace_id, base_url=base_url)
        assert res.status_code == 204, (
            f"Admin API 删除工作空间失败: {res.status_code}, {res.text[:300]}"
        )
        return res

    @staticmethod
    def list_members_success(
        secret_key,
        base_url=None,
        name=None,
        email=None,
        status=None,
        page=1,
        limit=10,
    ):
        res = list_members(
            secret_key,
            base_url=base_url,
            name=name,
            email=email,
            status=status,
            page=page,
            limit=limit,
        )
        assert res.status_code == 200, (
            f"Admin API 获取成员列表失败: {res.status_code}, {res.text[:300]}"
        )
        assert res.text and res.text.strip(), "Admin API members 列表 body 为空"
        return res.json()

    @staticmethod
    def create_member_success(
        secret_key,
        name,
        email,
        base_url=None,
        password=None,
        interface_language="en-US",
        timezone="America/New_York",
    ):
        """POST Admin API /members，返回 200 与 JSON，且包含 member id。"""
        res = create_member(
            secret_key,
            name=name,
            email=email,
            base_url=base_url,
            password=password,
            interface_language=interface_language,
            timezone=timezone,
        )
        assert res.status_code == 200, (
            f"Admin API 创建成员失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        member_id = AdminService._member_id_from_reply(data)
        assert member_id, f"Admin API 创建成员响应中未解析到 id: {data}"
        return data, member_id

    @staticmethod
    def get_member_success(secret_key, member_id, base_url=None):
        """GET Admin API /members/{id}，返回 200 且 id 与请求一致。"""
        res = get_member(secret_key, member_id, base_url=base_url)
        assert res.status_code == 200, (
            f"Admin API 获取成员失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        resolved_id = AdminService._member_id_from_reply(data)
        assert resolved_id == member_id, (
            f"Admin API 成员详情 id 与请求不一致: 期望 {member_id}, 解析 {resolved_id}, body: {data}"
        )
        return data

    @staticmethod
    def update_member_success(
        secret_key,
        member_id,
        base_url=None,
        name=None,
        email=None,
        status=None,
        password=None,
        interface_language=None,
        timezone=None,
    ):
        """PUT Admin API /members/{id}，返回 200；若传入 name/email/status 则校验响应字段。"""
        res = update_member(
            secret_key,
            member_id,
            base_url=base_url,
            name=name,
            email=email,
            status=status,
            password=password,
            interface_language=interface_language,
            timezone=timezone,
        )
        assert res.status_code == 200, (
            f"Admin API 更新成员失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        m = AdminService._member_dict_from_reply(data)
        assert m, f"Admin API 更新成员响应中未解析到 member: {data}"
        assert m.get("id") == member_id, f"Admin API 更新后 member.id 与请求不一致: {m}"
        if name is not None:
            assert m.get("name") == name, f"Admin API 更新后 name 不符合预期: {m}"
        if email is not None:
            assert m.get("email") == email, f"Admin API 更新后 email 不符合预期: {m}"
        if status is not None:
            assert m.get("status") == status, f"Admin API 更新后 status 不符合预期: {m}"
        return data

    @staticmethod
    def delete_member_success(secret_key, member_id, base_url=None):
        """DELETE Admin API /members/{id}，成功常见为 200 或 204。"""
        res = delete_member(secret_key, member_id, base_url=base_url)
        assert res.status_code in (200, 204), (
            f"Admin API 删除成员失败: {res.status_code}, {res.text[:300]}"
        )
        return res

    @staticmethod
    def list_workspace_members_success(
        secret_key,
        workspace_id,
        base_url=None,
        workspace_role=None,
        page=1,
        limit=10,
    ):
        res = list_workspace_members(
            secret_key,
            workspace_id,
            base_url=base_url,
            workspace_role=workspace_role,
            page=page,
            limit=limit,
        )
        assert res.status_code == 200, (
            f"Admin API 获取工作空间成员列表失败: {res.status_code}, {res.text[:300]}"
        )
        assert res.text and res.text.strip(), "Admin API workspace members 列表 body 为空"
        return res.json()

    @staticmethod
    def get_workspace_member_success(secret_key, workspace_id, member_id, base_url=None):
        res = get_workspace_member(
            secret_key,
            workspace_id,
            member_id,
            base_url=base_url,
        )
        assert res.status_code == 200, (
            f"Admin API 获取工作空间成员失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        resolved = AdminService._workspace_member_member_id_from_reply(data)
        assert resolved == member_id, (
            f"Admin API 工作空间成员 member_id 与请求不一致: 期望 {member_id}, 解析 {resolved}, body: {data}"
        )
        return data

    @staticmethod
    def add_workspace_member_success(
        secret_key,
        workspace_id,
        member_id,
        workspace_role,
        base_url=None,
    ):
        res = add_workspace_member(
            secret_key,
            workspace_id,
            member_id,
            workspace_role,
            base_url=base_url,
        )
        assert res.status_code == 200, (
            f"Admin API 添加工作空间成员失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        role = AdminService._workspace_role_from_reply(data)
        if role is not None:
            assert role == workspace_role, (
                f"Admin API 添加成员后 workspace_role 不符合预期: {data}"
            )
        return data

    @staticmethod
    def update_workspace_member_success(
        secret_key,
        workspace_id,
        member_id,
        workspace_role,
        base_url=None,
    ):
        res = update_workspace_member(
            secret_key,
            workspace_id,
            member_id,
            workspace_role,
            base_url=base_url,
        )
        assert res.status_code == 200, (
            f"Admin API 更新工作空间成员失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        role = AdminService._workspace_role_from_reply(data)
        if role is not None:
            assert role == workspace_role, (
                f"Admin API 更新成员后 workspace_role 不符合预期: {data}"
            )
        return data

    @staticmethod
    def delete_workspace_member_success(secret_key, workspace_id, member_id, base_url=None):
        res = delete_workspace_member(
            secret_key,
            workspace_id,
            member_id,
            base_url=base_url,
        )
        assert res.status_code in (200, 204), (
            f"Admin API 移除工作空间成员失败: {res.status_code}, {res.text[:300]}"
        )
        return res

    @staticmethod
    def list_groups_success(secret_key, base_url=None, name=None, page=1, limit=10):
        res = list_groups(
            secret_key,
            base_url=base_url,
            name=name,
            page=page,
            limit=limit,
        )
        assert res.status_code == 200, (
            f"Admin API 获取用户组列表失败: {res.status_code}, {res.text[:300]}"
        )
        assert res.text and res.text.strip(), "Admin API groups 列表 body 为空"
        return res.json()

    @staticmethod
    def create_group_success(secret_key, name, base_url=None):
        """POST Admin API /groups，返回 200 且含 group id。"""
        res = create_group(secret_key, name, base_url=base_url)
        assert res.status_code == 200, (
            f"Admin API 创建用户组失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        group_id = AdminService._group_id_from_reply(data)
        assert group_id, f"Admin API 创建 group 响应中未解析到 id: {data}"
        return data, group_id

    @staticmethod
    def get_group_success(secret_key, group_id, base_url=None):
        res = get_group(secret_key, group_id, base_url=base_url)
        assert res.status_code == 200, (
            f"Admin API 获取用户组失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        resolved = AdminService._group_id_from_reply(data)
        assert resolved == group_id, (
            f"Admin API 用户组 id 与请求不一致: 期望 {group_id}, 解析 {resolved}, body: {data}"
        )
        return data

    @staticmethod
    def update_group_success(secret_key, group_id, name, base_url=None):
        res = update_group(secret_key, group_id, name, base_url=base_url)
        assert res.status_code == 200, (
            f"Admin API 更新用户组失败: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text and res.text.strip() else {}
        g = AdminService._group_dict_from_reply(data)
        assert g, f"Admin API 更新 group 响应中未解析到 group: {data}"
        assert g.get("id") == group_id, f"Admin API 更新后 group.id 与请求不一致: {g}"
        assert g.get("name") == name, f"Admin API 更新后 name 不符合预期: {g}"
        return data

    @staticmethod
    def delete_group_success(secret_key, group_id, base_url=None):
        res = delete_group(secret_key, group_id, base_url=base_url)
        assert res.status_code in (200, 204), (
            f"Admin API 删除用户组失败: {res.status_code}, {res.text[:300]}"
        )
        return res

    @staticmethod
    def list_group_members_success(secret_key, group_id, base_url=None, page=1, limit=10):
        res = list_group_members(
            secret_key,
            group_id,
            base_url=base_url,
            page=page,
            limit=limit,
        )
        assert res.status_code == 200, (
            f"Admin API 获取用户组成员列表失败: {res.status_code}, {res.text[:300]}"
        )
        assert res.text and res.text.strip(), "Admin API group members 列表 body 为空"
        return res.json()

    @staticmethod
    def add_group_member_success(secret_key, group_id, member_id, base_url=None):
        res = add_group_member(
            secret_key,
            group_id,
            member_id,
            base_url=base_url,
        )
        assert res.status_code == 200, (
            f"Admin API 添加用户组成员失败: {res.status_code}, {res.text[:300]}"
        )
        return res.json() if res.text and res.text.strip() else {}

    @staticmethod
    def delete_group_member_success(secret_key, group_id, member_id, base_url=None):
        res = delete_group_member(
            secret_key,
            group_id,
            member_id,
            base_url=base_url,
        )
        assert res.status_code in (200, 204), (
            f"Admin API 移除用户组成员失败: {res.status_code}, {res.text[:300]}"
        )
        return res

    @staticmethod
    def _app_id_from_import_dsl_reply(data):
        if not isinstance(data, dict):
            return None
        for key in ("app_id", "appId"):
            if data.get(key):
                return data.get(key)
        app = data.get("app")
        if isinstance(app, dict):
            rid = app.get("id") or app.get("app_id") or app.get("appId")
            if rid:
                return rid
        if data.get("id") is not None:
            return data.get("id")
        return None

    @staticmethod
    def import_workspace_dsl_success(
        secret_key,
        workspace_id,
        creator_email,
        name,
        description,
        file_path,
        base_url=None,
    ):
        """POST Admin API /workspaces/{id}/dsl/import（multipart），返回 200 与 JSON。"""
        res = import_workspace_dsl(
            secret_key,
            workspace_id,
            creator_email,
            name,
            description,
            file_path,
            base_url=base_url,
        )
        assert res.status_code == 200, (
            f"Admin API 导入工作空间 DSL 失败: {res.status_code}, {res.text[:500]}"
        )
        assert res.text and res.text.strip(), "Admin API 导入 DSL 响应 body 为空"
        return res.json()

    @staticmethod
    def export_app_dsl_success(secret_key, app_id, base_url=None, include_secret=False):
        """GET Admin API /apps/{app_id}/dsl?include_secret=…，返回 200 与非空 body（多为 YAML 文本）。"""
        res = export_app_dsl(
            secret_key,
            app_id,
            base_url=base_url,
            include_secret=include_secret,
        )
        assert res.status_code == 200, (
            f"Admin API 导出应用 DSL 失败: {res.status_code}, {res.text[:500]}"
        )
        assert res.text and res.text.strip(), "Admin API 导出 DSL body 为空"
        return res
