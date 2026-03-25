from common.config import config

# Console：base 使用 CONSOLE_URL（如 https://console-platform.dify.dev）
_CONSOLE_API_BASE = f"{(config.console_url or '').rstrip('/')}/console/api"
_APPS_BASE = f"{_CONSOLE_API_BASE}/apps"
APPS_IMPORTS_PATH = f"{_APPS_BASE}/imports"


def _app_by_id_path(app_id):
    """DELETE /console/api/apps/{app_id} 等。"""
    return f"{_APPS_BASE}/{app_id}"

def _app_draft_path(app_id):
    return f"{_APPS_BASE}/{app_id}/workflows/draft"

def _app_publish_path(app_id):
    return f"{_APPS_BASE}/{app_id}/workflows/publish"


def import_app(client, mode="yaml-content", yaml_content=None, **payload):
    """
    POST /console/api/apps/imports
    导入应用（YAML 等）。
    payload: mode（如 yaml-content）, yaml_content（YAML 字符串），或通过 **payload 传入完整 body。
    response 示例: {"id": "...", "status": "completed", "app_id": "...", "app_mode": "workflow", ...}
    """
    if payload:
        body = payload
    else:
        body = {"mode": mode, "yaml_content": yaml_content or ""}
    return client.post(APPS_IMPORTS_PATH, json=body)


def delete_app(client, app_id):
    """
    DELETE /console/api/apps/{app_id}
    删除应用，无 request body。
    """
    return client.delete(_app_by_id_path(app_id))


def publish_app(client, app_id, marked_name="", marked_comment="", **payload):
    """
    POST /console/api/apps/{app_id}/workflows/publish
    发布应用工作流。
    payload 可选：marked_name, marked_comment；不传则 body 为空或 {}。
    response 示例: {"result": "success", "created_at": 1773913615}
    """
    if payload:
        body = payload
    else:
        body = {"marked_name": marked_name, "marked_comment": marked_comment}
    return client.post(_app_publish_path(app_id), json=body)


def get_workflow_draft(client, app_id):
    path = _app_draft_path(app_id)
    return client.get(path)

def update_workflow_draft(client, app_id, **payload):
    path = _app_draft_path(app_id)
    return client.post(path, json=payload)