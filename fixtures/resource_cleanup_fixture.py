import os

import pytest

from api.apps_api import delete_app, import_app, publish_app
from api.workspace_api import delete_default_workspace, get_default_workspace
from api.console_api import (
    delete_workspace_builtin_tool_credential,
    delete_workspace_model_provider_credential,
)
from api.credentials_api import update_credential_policy
from api.password_policy import reset_password
from api.plugin_api import (
    extract_installed_tenant_ids,
    find_install_task_status_by_id,
    find_plugin_by_ids,
    list_plugin_ids,
)
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


@pytest.fixture
def restore_password_policy_after_policy_test(admin_client):
    """
    仅用于「修改密码策略后需回滚环境」的用例（如 ``test_update_password_policy_and_login``）。

    在**该用例结束后**执行：恢复默认密码策略，并将 ``PWD_EMAIL`` 账号密码从
    ``NEW_PASSWORD_AFTER_POLICY`` 改回 ``PWD_PASSWORD``（需同时配置上述环境变量）。
    不注入本 fixture 时，其它使用 ``resource_tracker`` 的用例不会在 session teardown 中触发该逻辑。
    """
    yield
    try:
        email = os.getenv("PWD_EMAIL")
        current_password = os.getenv("NEW_PASSWORD_AFTER_POLICY")
        new_password = os.getenv("PWD_PASSWORD")
        if not email or not current_password or not new_password:
            return
        password_svc = PasswordService()
        password_svc.update_password_policy_success(client=admin_client)
        member_client, _ = AuthService.admin_login(
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


@pytest.fixture
def ensure_no_default_workspace(admin_client):
    """
    查询 GET /dashboard/api/default-workspace：
    - 若为「无默认」形态（如 ``workspaceId`` 为空且 ``workspace`` 为 ``null``），则不做任何事；
    - 若存在有效默认工作空间（非空 ``workspaceId`` 且 ``workspace`` 为对象等），则 DELETE 取消默认工作空间。

    需要干净默认工作空间状态的用例请注入本 fixture。
    """
    res = get_default_workspace(admin_client)
    if res.status_code != 200:
        return
    try:
        data = res.json() if res.text and res.text.strip() else {}
    except Exception:
        return
    if not isinstance(data, dict):
        return
    raw_id = data.get("workspaceId")
    wid = "" if raw_id is None else str(raw_id).strip()
    ws = data.get("workspace")
    if wid == "" and ws is None:
        return
    del_res = delete_default_workspace(admin_client)
    assert del_res.status_code == 200, (
        f"取消默认 workspace 失败: {del_res.status_code}, {del_res.text[:300]}"
    )
    body = del_res.text.strip()
    assert not body or body in ("{}", "null"), (
        f"取消默认 workspace 成功时响应体应为空或 {{}}，实际: {del_res.text[:200]}"
    )


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
def created_member_workspace(admin_client, ensure_no_default_workspace):
    """先确保无默认工作空间，再创建成员与 workspace（owner 为该成员）；用例完成后先清理 workspace，再清理成员。yield (member_info, workspace_id)。"""
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
    # 若该 workspace 被设为默认，需先取消默认再删除，否则删除可能失败
    try:
        res = get_default_workspace(admin_client)
        if res.status_code == 200 and res.text and res.text.strip():
            data = res.json()
            if isinstance(data, dict):
                raw = data.get("workspaceId")
                wid = "" if raw is None else str(raw).strip()
                if wid and str(wid) == str(workspace_id):
                    delete_default_workspace(admin_client)
    except Exception:
        pass
    # 先清理 workspace，再清理成员
    try:
        workspace_svc.delete_workspace_success(workspace_id, admin_client)
    except Exception:
        pass
    member_svc.delete_member_success(member_id, admin_client)


@pytest.fixture(scope="session")
def plugin_pre_installed(admin_client, request):
    """
    插件前置安装 + 工作空间分配（幂等）。默认使用环境配置 PLUGIN_ID、PLUGIN_UNIQUE_IDENTIFIER、
    PLUGIN_SOURCE、PLUGIN_KEYWORD；用例中可通过 indirect 参数覆盖，并通过 ``tenant_id``（或
    ``workspace_id``）指定需要分配到的工作空间（租户）。

    执行逻辑：
    1. 通过 ``list_plugin_ids`` 判定插件是否已安装；
    2. 未安装：调用 ``install_plugin`` 并轮询安装任务至成功，随后 ``apply_plugin`` 分配到 ``tenant_id``；
    3. 已安装：从 ``installations`` 提取现有租户列表，若 ``tenant_id`` 已在其中则不做操作；
       否则 ``apply_plugin`` 以「现有租户 + tenant_id」整体下发，避免误卸载其它工作空间。
    未传 ``tenant_id`` 时仅做安装动作，不做分配。

    使用示例::

        @pytest.mark.parametrize(
            "plugin_pre_installed",
            [{
                "plugin_id": "langgenius/github",
                "plugin_unique_identifier": "langgenius/github:0.3.1@xxx",
                "source": "marketplace",
                "plugin_keyword": "github",
                "tenant_id": "f0435a59-fc6b-4d40-a478-6a53d00bb922",
            }],
            indirect=True,
        )
        def test_xxx(self, plugin_pre_installed): ...
    """
    plugin_svc = PluginService()
    overrides = getattr(request, "param", None) or {}
    plugin_id = overrides.get("plugin_id") or config.plugin_id
    plugin_unique_identifier = overrides.get("plugin_unique_identifier") or config.plugin_unique_identifier
    plugin_source = overrides.get("source") or overrides.get("plugin_source") or config.plugin_source
    plugin_keyword = overrides.get("plugin_keyword") or config.plugin_keyword
    tenant_id = (
        overrides.get("tenant_id")
        or overrides.get("tenantId")
        or overrides.get("workspace_id")
        or overrides.get("workspaceId")
    )

    def _build_result(found_entry, installed_tenants):
        return {
            "plugin_id": plugin_id,
            "plugin_unique_identifier": plugin_unique_identifier,
            "source": plugin_source,
            "pluginName": found_entry.get("pluginName") if found_entry else None,
            "pluginIcon": found_entry.get("pluginIcon") if found_entry else None,
            "pluginVersion": found_entry.get("version") if found_entry else None,
            "tenant_id": tenant_id,
            "installed_tenant_ids": list(installed_tenants),
        }

    if not plugin_id or not plugin_unique_identifier:
        yield _build_result(None, [])
        return

    def _query_plugin_entry():
        """
        查询并定位到**目标版本的插件子项**。

        ``list_plugin_ids`` 按关键字返回同一个 ``pluginId`` 下的**全部已安装版本**（每个版本
        含独立的 ``installations``）；此处通过 ``find_plugin_by_ids`` 先按 ``pluginId`` 再按
        ``pluginUniqueIdentifier`` 精确匹配到目标版本，未命中返回 ``None``。
        """
        res = list_plugin_ids(
            admin_client,
            keyword=plugin_keyword,
            page_number=1,
            results_per_page=10,
        )
        if res.status_code != 200:
            raise RuntimeError(f"list_plugin_ids 失败: {res.status_code}, {res.text[:300]}")
        data_list = (res.json() or {}).get("data") or []
        return find_plugin_by_ids(data_list, plugin_id, plugin_unique_identifier)

    def _wait_install_task(task_id):
        def _get_status():
            list_body = plugin_svc.list_install_task_results(admin_client)
            status = find_install_task_status_by_id(list_body, task_id)
            if status and status.lower() in (s.lower() for s in PLUGIN_INSTALL_TASK_STATUS_FAILED):
                raise AssertionError(f"安装任务失败, taskId={task_id}, status={status}")
            return status

        try:
            wait_until(
                _get_status,
                timeout=PLUGIN_INSTALL_TASK_TIMEOUT_SEC,
                interval=PLUGIN_INSTALL_TASK_POLL_INTERVAL_SEC,
                success_condition=lambda s: s and s.lower() in (x.lower() for x in PLUGIN_INSTALL_TASK_STATUS_SUCCESS),
            )
        except TimeoutError as e:
            raise RuntimeError(
                f"插件安装任务未在 {PLUGIN_INSTALL_TASK_TIMEOUT_SEC}s 内完成, taskId={task_id}"
            ) from e

    # found 已精确匹配到目标版本（pluginUniqueIdentifier 对应的那一项）
    found = _query_plugin_entry()

    if found is None:
        # 目标版本尚未安装：安装 runtime -> 轮询任务成功 -> 分配到目标工作空间
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
        _wait_install_task(task_id)
        found = _query_plugin_entry()

        if tenant_id:
            plugin_svc.apply_plugin_success(
                client=admin_client,
                pluginUniqueIdentifier=plugin_unique_identifier,
                tenantIds=[tenant_id],
            )
            # 刷新一次以获取最新 installations
            refreshed = _query_plugin_entry()
            if refreshed is not None:
                found = refreshed
    else:
        # 目标版本已安装：**只看该版本自身的 installations**（不同版本互相独立），
        # 若目标工作空间不在其中，则合并 "原租户 + 新租户" 一起 apply（避免误卸载其它工作空间）。
        if tenant_id:
            installed_tenants_for_version = extract_installed_tenant_ids(found)
            if tenant_id not in installed_tenants_for_version:
                merged_tenant_ids = list(
                    dict.fromkeys([*installed_tenants_for_version, tenant_id])
                )
                plugin_svc.apply_plugin_success(
                    client=admin_client,
                    pluginUniqueIdentifier=plugin_unique_identifier,
                    tenantIds=merged_tenant_ids,
                )
                refreshed = _query_plugin_entry()
                if refreshed is not None:
                    found = refreshed

    # 对外暴露的 installed_tenant_ids 只反映**目标版本**的安装情况
    installed_tenants = extract_installed_tenant_ids(found) if found else []
    yield _build_result(found, installed_tenants)


# 应用导入 fixture 使用的 YAML 文件路径（相对项目根目录，目录名为 recources）
_IMPORT_APP_BASE = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "test_data",
    "recources",
)
IMPORT_APP_YAML_PATH = os.path.join(_IMPORT_APP_BASE, "auto_test_tool_credential.yml")
IMPORT_MODEL_APP_YAML_PATH = os.path.join(_IMPORT_APP_BASE, "auto_test_model_credential.yml")


def _resolve_import_app_yaml_path(param):
    """
    解析 ``import_app_fixture`` 的 indirect 参数为 YAML 绝对路径。

    支持形态：
    - ``None``：默认使用 ``IMPORT_APP_YAML_PATH``（auto_test_tool_credential.yml）。
    - ``str``：若为绝对路径则直接使用；否则视为 ``test_data/recources/`` 下的文件名。
    - ``dict``：优先取 ``yaml_path``（绝对路径），否则取 ``yaml_file``（相对文件名），
      均为空时回退默认路径。
    """
    if param is None:
        return IMPORT_APP_YAML_PATH
    if isinstance(param, str):
        return param if os.path.isabs(param) else os.path.join(_IMPORT_APP_BASE, param)
    if isinstance(param, dict):
        yaml_path = param.get("yaml_path")
        if yaml_path:
            return yaml_path if os.path.isabs(yaml_path) else os.path.join(_IMPORT_APP_BASE, yaml_path)
        yaml_file = param.get("yaml_file")
        if yaml_file:
            return os.path.join(_IMPORT_APP_BASE, yaml_file)
    return IMPORT_APP_YAML_PATH


@pytest.fixture
def import_app_fixture(request):
    """
    登录 Console 到工作空间，按参数导入应用：读取指定 YAML 作为 yaml_content，调用 import_app，
    断言 status 为 completed；再 publish_app 发布工作流；yield 返回 app_id。用例结束后调用
    delete_app 删除该应用。

    支持通过 indirect 参数指定 YAML 文件（不传则默认 auto_test_tool_credential.yml）::

        @pytest.mark.parametrize(
            "import_app_fixture",
            ["auto_test_model_credential.yml"],
            indirect=True,
        )
        def test_xxx(self, import_app_fixture): ...

        # 也可传 dict：{"yaml_file": "auto_test_tool_credential.yml"} 或 {"yaml_path": "/abs/path.yml"}
    """
    yaml_path = _resolve_import_app_yaml_path(getattr(request, "param", None))
    client, _ = AuthService.console_login()
    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_content = f.read()
    res = import_app(client, mode="yaml-content", yaml_content=yaml_content)
    assert res.status_code == 200, f"导入应用失败: {res.status_code}, {res.text[:300]}"
    data = res.json() or {}
    assert data.get("status") == "completed", f"导入应用未完成: {data}"
    app_id = data.get("app_id")
    assert app_id, f"导入应用响应中未返回 app_id: {data}"
    # pub_res = publish_app(client, app_id)
    # assert pub_res.status_code == 200, f"发布应用失败: {pub_res.status_code}, {pub_res.text[:300]}"
    yield app_id
    try:
        delete_app(client, app_id)
    except Exception:
        pass
