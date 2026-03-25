from api.apps_api import (
    delete_app,
    get_workflow_draft,
    import_app,
    publish_app,
    update_workflow_draft,
)
from services.base_service import BaseService


class AppsService(BaseService):

    def import_app_success(self, client=None, mode="yaml-content", yaml_content=None, **payload):
        client = self.get_console_client(client)
        res = import_app(client, mode=mode, yaml_content=yaml_content, **payload)
        data = self.assert_and_parse(res, message="导入应用失败")
        app_id = data.get("app_id") or data.get("appId") or data.get("id")
        assert app_id, f"导入应用响应中缺少应用标识: {data}"
        return data

    def get_workflow_draft_success(self, app_id, client=None):
        client = self.get_console_client(client)
        res = get_workflow_draft(client, app_id)
        data = self.assert_and_parse(res, message="获取 workflow draft 失败")
        assert isinstance(data, dict), f"workflow draft 响应格式异常: {data}"
        return data

    def update_workflow_draft_success(self, app_id, client=None, **payload):
        client = self.get_console_client(client)
        res = update_workflow_draft(client, app_id, **payload)
        data = self.assert_and_parse(res, message="更新 workflow draft 失败")
        assert isinstance(data, dict), f"更新 workflow draft 响应格式异常: {data}"
        return data

    def publish_app_success(self, app_id, client=None, marked_name="", marked_comment="", **payload):
        client = self.get_console_client(client)
        res = publish_app(
            client,
            app_id,
            marked_name=marked_name,
            marked_comment=marked_comment,
            **payload,
        )
        data = self.assert_and_parse(res, message="发布应用失败")
        result = data.get("result")
        assert result in (None, "success"), f"发布应用结果异常: {data}"
        return data

    def delete_app_success(self, app_id, client=None):
        client = self.get_console_client(client)
        res = delete_app(client, app_id)
        self.assert_status_code(res, message="删除应用失败")
        body = res.text.strip()
        assert not body or body in ("{}", "null"), f"删除应用成功时响应体应为空，实际: {res.text[:200]}"
