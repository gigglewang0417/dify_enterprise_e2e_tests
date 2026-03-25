from common.request import Request
from common.config import config


class AuthAPI:

    @staticmethod
    def admin_login(email, password):

        url = f"{config.base_url}/dashboard/api/login"

        payload = {
            "email": email,
            "password": password
        }

        return Request.post(url, json=payload)

    @staticmethod
    def console_login(email, password, language="zh-Hans", remember_me=True):
        """Console 登录：POST /console/api/login，payload 含 language、remember_me。"""
        base = (config.console_url or "").rstrip("/")
        url = f"{base}/console/api/login"
        payload = {
            "email": email,
            "password": password,
            "language": language,
            "remember_me": remember_me,
        }
        return Request.post(url, json=payload)

    # ---------- Console SSO ----------
    @staticmethod
    def console_sso_oauth2_login():
        """GET /console/api/enterprise/sso/oauth2/login，ConsoleSSO_OAuth2Login。"""
        base = (config.console_url or "").rstrip("/")
        url = f"{base}/console/api/enterprise/sso/oauth2/login"
        return Request.get(url)

    @staticmethod
    def console_sso_oidc_login():
        """GET /console/api/enterprise/sso/oidc/login，ConsoleSSO_OIDCLogin。"""
        base = (config.console_url or "").rstrip("/")
        url = f"{base}/console/api/enterprise/sso/oidc/login"
        return Request.get(url)

    @staticmethod
    def console_sso_saml_login():
        """GET /console/api/enterprise/sso/saml/login，ConsoleSSO_SAMLLogin。"""
        base = (config.console_url or "").rstrip("/")
        url = f"{base}/console/api/enterprise/sso/saml/login"
        return Request.get(url)



