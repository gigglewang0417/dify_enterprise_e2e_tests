"""
Dify Console SAML SSO 登录工具：
1. 生成 SAML Assertion XML -> Base64 Encode
2. POST /console/api/enterprise/sso/saml/acs -> Dify 验证 Assertion，创建 session 并返回 Set-Cookie
3. 使用返回的 session（带 Cookie）调 Console API 验证登录成功
"""
import base64
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

import requests


# ==============================
# SAML 固定配置（可按环境覆盖）
# ==============================
# Service Provider Entity ID（Dify Console 在 IdP 中配置的 SP Entity ID）
SP_ENTITY_ID = os.getenv("SAML_SP_ENTITY_ID", "https://integrator-1700738.okta.com/app/integrator-1700738_uatinnerusersigninsmal_1/exkyf9t3wgmUJ1iTr697/sso/saml")
# IdP Issuer
IDP_ISSUER = os.getenv("SAML_IDP_ISSUER", "http://www.okta.com/exkwahq7dnHWaYODh697")
NAME_ID_FORMAT = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
# Dify SSO 属性映射字段
ATTRIBUTE_EMAIL = "user.email"


def get_acs_url(console_url: Optional[str] = None) -> str:
    """Dify Console SAML ACS 地址。"""
    base = (console_url or os.getenv("CONSOLE_URL") or "").rstrip("/")
    return f"{base}/console/api/enterprise/sso/saml/acs"


def generate_saml_response(email: str, console_url: Optional[str] = None) -> str:
    """
    步骤 1：生成 Mock SAML Response（Base64 编码）。
    :param email: 登录用户邮箱，如 auto_test@dify.ai
    :param console_url: Console 根 URL，默认从环境变量 CONSOLE_URL 读取
    :return: Base64 编码的 SAMLResponse，用于 POST 到 ACS
    """
    acs_url = get_acs_url(console_url)

    now = datetime.utcnow()
    issue_instant = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    not_before = (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    not_on_or_after = (now + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

    response_id = "_" + str(uuid.uuid4()).replace("-", "")
    assertion_id = "_" + str(uuid.uuid4()).replace("-", "")

    saml_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol" xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" ID="{response_id}" Version="2.0" IssueInstant="{issue_instant}" Destination="{acs_url}">
    <saml2:Issuer>{IDP_ISSUER}</saml2:Issuer>
    <saml2p:Status>
        <saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </saml2p:Status>
    <saml2:Assertion ID="{assertion_id}" Version="2.0" IssueInstant="{issue_instant}">
        <saml2:Issuer>{IDP_ISSUER}</saml2:Issuer>
        <saml2:Subject>
            <saml2:NameID Format="{NAME_ID_FORMAT}">{email}</saml2:NameID>
            <saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
                <saml2:SubjectConfirmationData NotOnOrAfter="{not_on_or_after}" Recipient="{acs_url}"/>
            </saml2:SubjectConfirmation>
        </saml2:Subject>
        <saml2:Conditions NotBefore="{not_before}" NotOnOrAfter="{not_on_or_after}">
            <saml2:AudienceRestriction>
                <saml2:Audience>{SP_ENTITY_ID}</saml2:Audience>
            </saml2:AudienceRestriction>
        </saml2:Conditions>
        <saml2:AuthnStatement AuthnInstant="{issue_instant}">
            <saml2:AuthnContext>
                <saml2:AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:Password</saml2:AuthnContextClassRef>
            </saml2:AuthnContext>
        </saml2:AuthnStatement>
        <saml2:AttributeStatement>
            <saml2:Attribute Name="{ATTRIBUTE_EMAIL}">
                <saml2:AttributeValue>{email}</saml2:AttributeValue>
            </saml2:Attribute>
        </saml2:AttributeStatement>
    </saml2:Assertion>
</saml2p:Response>"""

    # 仅做空白规范化，不经过 ET 避免命名空间被改写
    saml_clean = "\n".join(line.strip() for line in saml_xml.strip().splitlines() if line.strip())
    return base64.b64encode(saml_clean.encode("utf-8")).decode("utf-8")


def post_saml_acs(
    email: str,
    console_url: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> Tuple[requests.Session, requests.Response]:
    """
    步骤 2：将 SAMLResponse POST 到 Dify Console ACS，Dify 验证 Assertion 并创建用户 session、返回 Set-Cookie。
    :param email: 登录用户邮箱
    :param console_url: Console 根 URL，默认 CONSOLE_URL
    :param session: 可选，传入则使用该 session（便于拿到带 Cookie 的 session）；不传则新建
    :return: (session, response)，session 中已包含响应写入的 Cookie，可直接用于后续 Console API 请求
    """
    acs_url = get_acs_url(console_url)
    saml_base64 = generate_saml_response(email, console_url)

    if session is None:
        session = requests.Session()

    # SAML ACS 标准：application/x-www-form-urlencoded，表单字段 SAMLResponse（及可选 RelayState）
    data = {"SAMLResponse": saml_base64}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # 不跟随重定向，便于检查 302 的 Location 或 200 的 body
    response = session.post(acs_url, data=data, headers=headers, allow_redirects=True)

    return session, response


def verify_console_login_with_session(
    session: requests.Session,
    console_url: Optional[str] = None,
    path: str = "/console/api/me",
) -> requests.Response:
    """
    步骤 4：使用 ACS 返回的 session（带 Cookie）请求 Console API，验证登录是否成功。
    :param session: 已调用 post_saml_acs 得到的 session（带 Cookie）
    :param console_url: Console 根 URL
    :param path: 用于校验的 API 路径，默认 /console/api/me
    :return: 请求的 Response，调用方可根据 status_code 或 body 断言
    """
    base = (console_url or os.getenv("CONSOLE_URL") or "").rstrip("/")
    url = base + path if path.startswith("/") else f"{base}/{path}"
    return session.get(url)
