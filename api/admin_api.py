"""
Admin API：使用 secret key（Bearer）调用的接口，base 为 ADMIN_API_BASE_URL（如 https://xxx/admin-api/v1）
"""
import os

import requests

from common.config import config


def _admin_api_base(base_url=None):
    base = (base_url or getattr(config, "admin_api_base_url", None) or os.getenv("ADMIN_API_BASE_URL") or "").rstrip("/")
    return base


def list_workspaces(
    secret_key,
    base_url=None,
    name=None,
    status=None,
    page=1,
    limit=10,
):
    """
    GET {admin_api_base}/workspaces
    使用 Admin API secret key（Bearer）鉴权，获取工作空间列表。
    query: name, status, page, limit
    """
    base = _admin_api_base(base_url)
    url = f"{base}/workspaces"
    params = {}
    if name is not None:
        params["name"] = name
    if status is not None:
        params["status"] = status
    if page is not None:
        params["page"] = page
    if limit is not None:
        params["limit"] = limit
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    return requests.get(url, params=params if params else None, headers=headers)
