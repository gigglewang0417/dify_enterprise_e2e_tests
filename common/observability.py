import json
from typing import Any

from common.logger import get_logger

logger = get_logger()

SENSITIVE_KEYS = {
    "password",
    "currentpassword",
    "newpassword",
    "confirmpassword",
    "access_token",
    "refresh_token",
    "csrf_token",
    "authorization",
    "secretkey",
    "secret_key",
    "api_key",
    "openai_api_key",
    "dashscope_api_key",
    "access_tokens",
}


def _get_allure():
    try:
        import allure  # type: ignore

        return allure
    except Exception:
        return None


def mask_sensitive_data(value: Any):
    if isinstance(value, dict):
        masked = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                masked[key] = "***MASKED***"
            else:
                masked[key] = mask_sensitive_data(item)
        return masked
    if isinstance(value, list):
        return [mask_sensitive_data(item) for item in value]
    return value


def to_pretty_text(value: Any):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(mask_sensitive_data(value), ensure_ascii=False, indent=2, default=str)
    return str(value)


def attach_text(name: str, content: Any):
    text = to_pretty_text(content)
    if not text:
        return
    allure = _get_allure()
    if allure:
        allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_json(name: str, content: Any):
    text = to_pretty_text(content)
    if not text:
        return
    allure = _get_allure()
    if allure:
        allure.attach(text, name=name, attachment_type=allure.attachment_type.JSON)


def log_kv(title: str, data: Any):
    text = to_pretty_text(data)
    logger.info("%s\n%s", title, text)
    attach_text(title, text)


def log_http_interaction(method: str, url: str, kwargs=None, response=None, source="http"):
    request_payload = {
        "source": source,
        "method": method,
        "url": url,
        "params": (kwargs or {}).get("params"),
        "json": (kwargs or {}).get("json"),
        "data": (kwargs or {}).get("data"),
        "headers": (kwargs or {}).get("headers"),
    }
    logger.info("[%s] %s %s", source, method, url)
    attach_json(f"{source} request", request_payload)

    if response is None:
        return

    response_body = None
    try:
        response_body = response.json() if getattr(response, "text", "") else {}
    except Exception:
        response_body = getattr(response, "text", "")

    response_payload = {
        "status_code": getattr(response, "status_code", None),
        "headers": dict(getattr(response, "headers", {}) or {}),
        "body": response_body,
    }
    logger.info("[%s] response %s %s", source, getattr(response, "status_code", None), url)
    attach_json(f"{source} response", response_payload)
