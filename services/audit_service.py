from api.audit_log import list_events
from services.base_service import BaseService


def build_audit_log_query_params(
    start_time=None,
    end_time=None,
    workspace_id=None,
    resource_type=None,
    resource_id=None,
    operation_type=None,
    page_size=10,
    cursor=None,
    cursor_direction="CURSOR_DIRECTION_NEXT",
):
    """
    组装审计日志查询参数，用于 GET /v1/audit/logs。
    仅包含非 None 的项，便于与 list_events 等接口配合使用。
    """
    params = {}
    if start_time is not None:
        params["start_time"] = start_time
    if end_time is not None:
        params["end_time"] = end_time
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if resource_type is not None:
        params["resource_type"] = resource_type
    if resource_id is not None:
        params["resource_id"] = resource_id
    if operation_type is not None:
        params["operation_type"] = operation_type
    if page_size is not None:
        params["page_size"] = page_size
    if cursor is not None:
        params["cursor"] = cursor
    if cursor_direction is not None:
        params["cursor_direction"] = cursor_direction
    return params


class AuditService(BaseService):

    def list_events_success(
        self,
        client=None,
        start_time=None,
        end_time=None,
        workspace_id=None,
        resource_type=None,
        resource_id=None,
        operation_type=None,
        page_size=10,
        cursor=None,
        cursor_direction="CURSOR_DIRECTION_NEXT",
        **extra_params,
    ):
        """
        查询审计日志成功：GET /v1/audit/logs，断言 200，返回响应体。
        响应含 events（列表）、pagination（pageSize、nextCursor、prevCursor、hasNextPage、hasPrevPage）。
        若未传 client 则内部 admin_login()。
        参数会拼接到 URL query，例如 startTime、endTime、workspaceId、resourceType、pageSize、cursorDirection 等。
        """
        client = self.get_admin_client(client)
        kwargs = build_audit_log_query_params(
            start_time=start_time,
            end_time=end_time,
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            operation_type=operation_type,
            page_size=page_size,
            cursor=cursor,
            cursor_direction=cursor_direction,
        )
        kwargs.update(extra_params)
        res = list_events(client, **kwargs)
        data = self.assert_and_parse(res, message="查询审计日志失败")
        assert isinstance(data.get("events") or [], list), f"审计日志 events 字段格式异常: {data}"
        return data
