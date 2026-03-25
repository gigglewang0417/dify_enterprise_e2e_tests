from common.config import config

# 路径常量（与 OpenAPI EnterpriseSystem / EnterpriseSSO 一致）
ENTERPRISE_SYSTEM_USER_SETTING_PATH = f"{config.base_url}/v1/dashboard/api/enterprise-system-user-setting"
SYSTEM_USER_SETTING_PATH = f"{config.base_url}/v1/dashboard/api/system-user-setting"


def get_enterprise_system_user_setting(client):
    """
    GET /v1/dashboard/api/enterprise-system-user-setting
    EnterpriseSystem_GetEnterpriseSystemUserSetting
    response: EnterpriseSystemUserSettingReply
    """
    return client.get(ENTERPRISE_SYSTEM_USER_SETTING_PATH)


def get_system_user_setting(client):
    """
    GET /v1/dashboard/api/system-user-setting
    EnterpriseSSO_GetSystemUserSetting
    response: SystemUserSettingReply
    """
    return client.get(SYSTEM_USER_SETTING_PATH)


def update_system_user_setting(client, **payload):
    """
    POST /v1/dashboard/api/system-user-setting
    EnterpriseSSO_UpdateSystemUserSetting
    requestBody: SystemUserSettingReq (required)
    response: SystemUserSettingReply
    """
    return client.post(SYSTEM_USER_SETTING_PATH, json=payload)
