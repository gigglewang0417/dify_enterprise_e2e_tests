from common.config import config

# 路径常量（与 OpenAPI AuditLog 一致）
AUDIT_LOGS_PATH = f"{config.base_url}/audit/logs"


def list_events(
    client,
    start_time=None,
    end_time=None,
    workspace_id=None,
    resource_type=None,
    resource_id=None,
    operation_type=None,
    page_size=None,
    cursor=None,
    cursor_direction=None,
):
    """
    GET /v1/audit/logs
    AuditLog_ListEvents
    query: startTime, endTime, workspaceId, resourceType, resourceId, operationType, pageSize, cursor, cursorDirection
    response: ListEventsResponse
    """
    params = {}
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    if workspace_id is not None:
        params["workspaceId"] = workspace_id
    if resource_type is not None:
        params["resourceType"] = resource_type
    if resource_id is not None:
        params["resourceId"] = resource_id
    if operation_type is not None:
        params["operationType"] = operation_type
    if page_size is not None:
        params["pageSize"] = page_size
    if cursor is not None:
        params["cursor"] = cursor
    if cursor_direction is not None:
        params["cursorDirection"] = cursor_direction
    return client.get(AUDIT_LOGS_PATH, params=params if params else None)
