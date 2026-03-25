from common.config import config

# 路径常量（与 OpenAPI EnterprisePasswordPolicy / EnterpriseUser 一致）
PASSWORD_POLICY_PATH = f"{config.base_url}/dashboard/api/password/policy"
PASSWORD_STATUS_PATH = f"{config.base_url}/dashboard/api/password/status"
PASSWORD_STRENGTH_PATH = f"{config.base_url}/dashboard/api/password/strength"
RESET_PASSWORD_PATH = f"{config.base_url}/dashboard/api/reset-password"



def get_password_policy(client):
    """
    GET /v1/dashboard/api/password/policy
    EnterprisePasswordPolicy_GetPasswordPolicy
    response: PasswordPolicyConfig
    """
    return client.get(PASSWORD_POLICY_PATH)


def update_password_policy(client, **payload):
    """
    PUT /v1/dashboard/api/password/policy
    EnterprisePasswordPolicy_UpdatePasswordPolicy
    requestBody: PasswordPolicyConfig (required)
    response: PasswordPolicyConfig
    """
    return client.put(PASSWORD_POLICY_PATH, json=payload)


def check_password_status(client):
    """
    GET /v1/dashboard/api/password/status
    EnterpriseUser_CheckPasswordStatus
    response: CheckPasswordStatusReply
    """
    return client.get(PASSWORD_STATUS_PATH)


def get_password_strength(client, **payload):
    """
    POST /v1/dashboard/api/password/strength
    EnterprisePasswordPolicy_GetPasswordStrength
    requestBody: PasswordStrengthReq (required)
    response: PasswordStrengthReply
    """
    return client.post(PASSWORD_STRENGTH_PATH, json=payload)


def reset_password(client, **payload):
    """
    POST /v1/dashboard/api/reset-password
    EnterpriseUser_ResetPassword
    requestBody: ResetPasswordReq (required)
    response: ResetPasswordReply
    """
    return client.post(RESET_PASSWORD_PATH, json=payload)

