import os

import pytest

from api.apps_api import delete_app, import_app
from api.console_api import (
    delete_workspace_builtin_tool_credential,
    delete_workspace_model_provider_credential,
)
from api.credentials_api import update_credential_policy
from api.password_policy import reset_password
from api.plugin_api import find_install_task_status_by_id, find_plugin_by_ids, list_plugin_ids
from common.config import config
from services.auth_service import AuthService
from services.credential_service import CredentialService
from services.member_service import MemberService
from services.password_service import PasswordService
from services.plugin_service import PluginService
from services.secretkey_service import SecretKeyService
from services.user_service import UserService
from services.worksapce_service import WorkspaceService
from utils.encode_util import base64_encode
from utils.polling import wait_until
from utils.random_util import random_email, random_name

# 插件前置安装轮询配置
PLUGIN_INSTALL_TASK_POLL_INTERVAL_SEC = 3
PLUGIN_INSTALL_TASK_TIMEOUT_SEC = 60
PLUGIN_INSTALL_TASK_STATUS_SUCCESS = ("success", "completed", "succeeded")
PLUGIN_INSTALL_TASK_STATUS_FAILED = ("failed", "error")

# 工具凭据策略：允许所有工具使用自定义 token（前置）
CREDENTIAL_POLICY_TOOLS_ALL_ALLOWED_PAYLOAD = {
    "type": "CREDENTIAL_TYPE_PLUGIN",
    "allowToolsUseCustomToken": True,
    "exceptToolPlugins": [],
    "allowModelsUseCustomToken": False,
    "exceptModelPlugins": [],
}
CREDENTIAL_POLICY_MODEL_ALL_ALLOWED_PAYLOAD = {
    "type": "CREDENTIAL_TYPE_MODEL",
    "allowToolsUseCustomToken": False,
    "exceptToolPlugins": [],
    "allowModelsUseCustomToken": True,
    "exceptModelPlugins": [],
}

class ResourceTracker:

    def __init__(self):
        self.members = []
        self.workspaces = []
        self.users = []
        self.plugins = []  # 待卸载的插件 payload 列表，每项为 dict，如 {"pluginUniqueIdentifier": "..."}
        self.secret_key_id = []
        self.credentials = []
        self.builtin_tool_credential = []
        # (credential_id, provider_path) 工作空间模型提供商自定义凭据
        self.workspace_model_credentials = []

    def add_member(self, member_id):
        self.members.append(member_id)

    def add_workspace(self, workspace_id):
        self.workspaces.append(workspace_id)

    def add_user(self, user_id):
        self.users.append(user_id)

    def add_plugin(self, **payload):
        """登记插件卸载 payload，cleanup 时会调用 uninstall_plugin_success(client, **payload)。"""
        self.plugins.append(payload)

    def reset_password(self):
        pass

    def add_secert_key(self, secret_key_id):
        self.secret_key_id.append(secret_key_id)

    def add_credential(self, credential_id):
        self.credentials.append(credential_id)

    def add_builtin_tool_credential(self, credential_id):
        self.builtin_tool_credential.append(credential_id)

    def add_workspace_model_credential(self, credential_id, provider_path="langgenius/tongyi/tongyi"):
        self.workspace_model_credentials.append((credential_id, provider_path))

    def cleanup(self, admin_client, console_client=None):
        """console_client：用于删除工作空间内置工具凭据；不传则在有 builtin_tool_credential 时内部 console_login。"""

        member_svc = MemberService()
        workspace_svc = WorkspaceService()
        user_svc = UserService()
        plugin_svc = PluginService()
        password_svc = PasswordService()
        secret_key_svc = SecretKeyService()
        credential_svc = CredentialService()

        for wid in self.workspaces:
            workspace_svc.delete_workspace_success(wid, admin_client)

        for mid in self.members:
            member_svc.delete_member_success(mid, admin_client)

        for uid in self.users:
            user_svc.delete_user_success(uid, admin_client)

        # 清理插件资源：按用例登记的 payload 逐个卸载
        for payload in self.plugins:
            try:
                plugin_svc.uninstall_plugin_success(client=admin_client, **payload)
            except Exception:
                pass

        # 恢复密码策略为默认，并将管理员密码恢复为 PWD_PASSWORD
        try:
            password_svc.update_password_policy_success(client=admin_client)
            email = os.getenv("PWD_EMAIL")
            current_password = os.getenv("NEW_PASSWORD_AFTER_POLICY")
            new_password = os.getenv("PWD_PASSWORD")
            member_client, login_res = AuthService.admin_login(
                email=email,
                password=base64_encode(current_password),
            )
            password_svc.reset_password_success(
                client=member_client,
                currentPassword=current_password,
                newPassword=new_password,
                confirmPassword=new_password,
            )
        except Exception:
            pass

        for skid in self.secret_key_id:
            secret_key_svc.delete_secret_key_success(skid, admin_client)

        for cid in self.credentials:
            credential_svc.delete_credential_success(cid, admin_client)

        # 清理工作空间内置工具自定义凭据（需 Console 登录态）
        client_console = console_client
        if self.builtin_tool_credential and client_console is None:
            try:
                client_console, _ = AuthService.console_login()
            except Exception:
                client_console = None
        if client_console:
            for cid in self.builtin_tool_credential:
                try:
                    delete_workspace_builtin_tool_credential(client_console, cid)
                except Exception:
                    pass
            for cid, ppath in self.workspace_model_credentials:
                try:
                    delete_workspace_model_provider_credential(client_console, cid, provider_path=ppath)
                except Exception:
                    pass


@pytest.fixture(scope="class")
def admin_api_p0_secret_key(request, admin_client):
    """
    Admin API E2E（如 TestE2ECase5P0）：企业后台创建 secret key，yield secret_key_id；
    该类下用例全部结束后删除该密钥。
    用例内通过 self.admin_api_secret_key 获取 Bearer 的 secretKey 字符串。
    """
    secret_svc = SecretKeyService()
    body = secret_svc.create_secret_key_success(client=admin_client)
    secret_key = body.get("secretKey")
    secret_key_id = body.get("id")
    assert secret_key, f"创建 secret key 响应中未返回 secretKey: {body}"
    assert secret_key_id, f"创建 secret key 响应中未返回 id: {body}"
    request.cls.admin_api_secret_key = secret_key
    yield secret_key_id
    try:
        secret_svc.delete_secret_key_success(secret_key_id, admin_client)
    except Exception:
        pass


@pytest.fixture(scope="session")
def resource_tracker(admin_client, console_client):
    tracker = ResourceTracker()
    yield tracker
    tracker.cleanup(admin_client, console_client)


@pytest.fixture(scope="session")
def credential_tools_policy__all_allowed(admin_client):
    """
    前置：将工具凭据策略调整为「允许工具使用自定义 token」且例外列表为空（所有工具允许）。
    调用 PUT /v1/plugin-manager/credential-policies（update_credential_policy）。
    用例中需要此策略时注入本 fixture 即可（session 内只执行一次）。
    """
    res = update_credential_policy(
        admin_client,
        **CREDENTIAL_POLICY_TOOLS_ALL_ALLOWED_PAYLOAD,
    )
    assert res.status_code == 200, f"更新凭据策略失败: {res.status_code}, {res.text[:300]}"
    data = res.json() if res.text else {}
    yield data

@pytest.fixture(scope="session")
def credential_model_policy__all_allowed(admin_client):
    """
    前置：将模型凭据策略调整为「允许模型使用自定义 token」且例外列表为空（所有模型允许）。
    调用 PUT /v1/plugin-manager/credential-policies（update_credential_policy）。
    用例中需要此策略时注入本 fixture 即可（session 内只执行一次）。
    """
    res = update_credential_policy(
        admin_client,
        **CREDENTIAL_POLICY_MODEL_ALL_ALLOWED_PAYLOAD,
    )
    assert res.status_code == 200, f"更新凭据策略失败: {res.status_code}, {res.text[:300]}"
    data = res.json() if res.text else {}
    yield data


@pytest.fixture
def created_member(admin_client):
    """创建成员，yield 成员信息给用例使用，用例结束后删除该成员。"""
    member_svc = MemberService()
    email = random_email()
    name = random_name()
    data = member_svc.create_member_success(email=email, name=name, client=admin_client)
    member_id = data.get("id") or (data.get("member") or {}).get("id")
    member_info = {"id": member_id, "email": email, "data": data}
    yield member_info
    member_svc.delete_member_success(member_id, admin_client)


@pytest.fixture
def created_member_workspace(admin_client):
    """先创建成员，再创建 workspace（owner 为该成员）；用例完成后先清理 workspace，再清理成员。yield (member_info, workspace_id)。"""
    member_svc = MemberService()
    workspace_svc = WorkspaceService()
    email = random_email()
    name = random_name()
    data = member_svc.create_member_success(email=email, name=name, client=admin_client)
    member_id = data.get("id") or (data.get("member") or {}).get("id")
    member_password = data.get("password") or (data.get("member") or {}).get("password") or ""
    member_info = {"id": member_id, "email": email, "password": member_password, "data": data}
    workspace = workspace_svc.create_workspace_success(
        name=random_name(),
        status="normal",
        email=email,
        client=admin_client,
    )
    workspace_id = workspace.get("id")
    yield member_info, workspace_id
    # 先清理 workspace，再清理成员
    try:
        workspace_svc.delete_workspace_success(workspace_id, admin_client)
    except Exception:
        pass
    member_svc.delete_member_success(member_id, admin_client)


@pytest.fixture(scope="session")
def plugin_pre_installed(admin_client, request):
    """
    插件前置安装。默认使用环境配置 PLUGIN_ID、PLUGIN_UNIQUE_IDENTIFIER、PLUGIN_SOURCE、PLUGIN_KEYWORD。
    若用例需要安装不同插件，可用间接参数覆盖，例如：
        @pytest.mark.parametrize("plugin_pre_installed", [{"plugin_id": "langgenius/github", "plugin_unique_identifier": "langgenius/github:0.3.1@xxx", "source": "marketplace", "plugin_keyword": "github"}], indirect=True)
        def test_xxx(self, plugin_pre_installed): ...
    """
    plugin_svc = PluginService()
    overrides = getattr(request, "param", None) or {}
    plugin_id = overrides.get("plugin_id") or config.plugin_id
    plugin_unique_identifier = overrides.get("plugin_unique_identifier") or config.plugin_unique_identifier
    plugin_source = overrides.get("source") or overrides.get("plugin_source") or config.plugin_source
    plugin_keyword = overrides.get("plugin_keyword") or config.plugin_keyword

    if not plugin_id or not plugin_unique_identifier:
        yield {
            "plugin_id": plugin_id,
            "plugin_unique_identifier": plugin_unique_identifier,
            "source": plugin_source,
            "pluginName": None,
            "pluginIcon": None,
            "pluginVersion": None,
        }
        return

    # 1. 查询插件是否已安装：list_plugin_ids(keyword=..., pageNumber=1, resultsPerPage=10)
    res = list_plugin_ids(
        admin_client,
        keyword=plugin_keyword,
        page_number=1,
        results_per_page=10,
    )
    if res.status_code != 200:
        raise RuntimeError(f"list_plugin_ids 失败: {res.status_code}, {res.text[:300]}")
    body = res.json() or {}
    data = body.get("data") or []
    found = find_plugin_by_ids(data, plugin_id, plugin_unique_identifier)
    if found is None:
        # 2. 未安装则执行安装，轮询安装任务直至成功
        install_body = plugin_svc.install_plugin_success(
            client=admin_client,
            pluginUniqueIdentifier=plugin_unique_identifier,
            source=plugin_source,
        )
        task_id = install_body.get("task_id") or install_body.get("taskId")
        if isinstance(install_body.get("taskIds"), list) and install_body["taskIds"]:
            task_id = task_id or install_body["taskIds"][0]
        if not task_id:
            raise RuntimeError(f"安装插件响应中未返回 task_id/taskIds: {install_body}")

        def get_task_status():
            list_body = plugin_svc.list_install_task_results(admin_client)
            status = find_install_task_status_by_id(list_body, task_id)
            if status and status.lower() in (s.lower() for s in PLUGIN_INSTALL_TASK_STATUS_FAILED):
                raise AssertionError(f"安装任务失败, taskId={task_id}, status={status}")
            return status

        try:
            wait_until(
                get_task_status,
                timeout=PLUGIN_INSTALL_TASK_TIMEOUT_SEC,
                interval=PLUGIN_INSTALL_TASK_POLL_INTERVAL_SEC,
                success_condition=lambda s: s and s.lower() in (x.lower() for x in PLUGIN_INSTALL_TASK_STATUS_SUCCESS),
            )
        except TimeoutError as e:
            raise RuntimeError(f"插件安装任务未在 {PLUGIN_INSTALL_TASK_TIMEOUT_SEC}s 内完成, taskId={task_id}") from e
        # 安装完成后再查一次，拿到插件详情
        res = list_plugin_ids(admin_client, keyword=plugin_keyword, page_number=1, results_per_page=10)
        if res.status_code == 200:
            data = (res.json() or {}).get("data") or []
            found = find_plugin_by_ids(data, plugin_id, plugin_unique_identifier)

    # 无论是否已安装，都返回插件信息（含 pluginId, pluginName, pluginIcon, pluginVersion）
    plugin_name = found.get("pluginName") if found else None
    plugin_icon = found.get("pluginIcon") if found else None
    plugin_version = found.get("version") if found else None
    yield {
        "plugin_id": plugin_id,
        "plugin_unique_identifier": plugin_unique_identifier,
        "source": plugin_source,
        "pluginName": plugin_name,
        "pluginIcon": plugin_icon,
        "pluginVersion": plugin_version,
    }


# 应用导入 fixture 使用的 YAML 文件路径（相对项目根目录，目录名为 recources）
_IMPORT_APP_BASE = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "test_data",
    "recources",
)
IMPORT_APP_YAML_PATH = os.path.join(_IMPORT_APP_BASE, "auto_test_tool_credential.yml")
IMPORT_MODEL_APP_YAML_PATH = os.path.join(_IMPORT_APP_BASE, "auto_test_model_credential.yml")


@pytest.fixture
def import_app_fixture():
    """
    登录 Console 到工作空间，导入应用：读取 test_data/recources/auto_test_tool_credential.yml 作为 yaml_content，
    调用 import_app，断言 status 为 completed，yield 返回 response 中的 app_id。
    用例结束后调用 delete_app 删除该应用。
    """
    client, _ = AuthService.console_login()
    with open(IMPORT_APP_YAML_PATH, "r", encoding="utf-8") as f:
        yaml_content = f.read()
    res = import_app(client, mode="yaml-content", yaml_content=yaml_content)
    assert res.status_code == 200, f"导入应用失败: {res.status_code}, {res.text[:300]}"
    data = res.json() or {}
    assert data.get("status") == "completed", f"导入应用未完成: {data}"
    app_id = data.get("app_id")
    assert app_id, f"导入应用响应中未返回 app_id: {data}"
    yield app_id
    try:
        delete_app(client, app_id)
    except Exception:
        pass


@pytest.fixture
def import_model_app_fixture():
    """
    导入通义工作流应用：读取 auto_test_model_credential.yml，yield app_id，结束后 delete_app。
    """
    client, _ = AuthService.console_login()
    with open(IMPORT_MODEL_APP_YAML_PATH, "r", encoding="utf-8") as f:
        yaml_content = f.read()
    res = import_app(client, mode="yaml-content", yaml_content=yaml_content)
    assert res.status_code == 200, f"导入应用失败: {res.status_code}, {res.text[:300]}"
    data = res.json() or {}
    assert data.get("status") == "completed", f"导入应用未完成: {data}"
    app_id = data.get("app_id")
    assert app_id, f"导入应用响应中未返回 app_id: {data}"
    yield app_id
    try:
        delete_app(client, app_id)
    except Exception:
        pass

