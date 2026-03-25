"""
凭据管理
E2E P0：创建凭据 -> 分配凭据到工作空间（凭据正常使用）
"""
import copy
import os

import allure
import pytest
from services.apps_service import AppsService
from services.console_service import ConsoleService
from services.credential_service import CredentialService
from utils.test_log import log_resource_ids, log_step_data, log_step_result
from utils.random_util import random_name

ALLOCATED_TENANT_ID = "f0435a59-fc6b-4d40-a478-6a53d00bb922"

TOOL_CREDENTIAL_KEY = os.getenv("TOOL_CREDENTIAL_KEY", "test-github-token")
NEW_TOOL_CREDENTIAL_KEY = os.getenv("NEW_TOOL_CREDENTIAL_KEY", "test-github-token-updated")

GENERAL_MODEL_CREDENTIAL_KEY = os.getenv("GENERAL_MODEL_CREDENTIAL_KEY", "test-general-model-key")
GENERAL_MODEL_GENERAL = "GENERAL_MODEL_GENERAL"
GENERAL_MODEL_CUSTOMER = "GENERAL_MODEL_CUSTOMER"
CUSTOMER_MODEL_NAME = "ft:gpt-4.1-nano-2025-04-14:personal:minco:CAuif2nh"
CUSTOMER_MODEL_CREDENTIAL_KEY = os.getenv("CUSTOMER_MODEL_CREDENTIAL_KEY", "test-openai-model-key")

TONGYI_PROVIDER_PATH = "langgenius/tongyi"
DASHSCOPE_SECRET = os.getenv("DASHSCOPE_SECRET", "test-dashscope-key")

def _build_draft_update_with_tool_credential(draft_body, credential_id):
    """
    从 GET draft 响应中取出 graph、features、hash、environment_variables、conversation_variables，
    在 graph.nodes 里找到 data.type == tool 的节点，写入 credential_id / credentialId，
    拼成 update_workflow_draft 所需的 body（仅含上述字段，避免把 id/created_at 等无关字段一并提交）。
    """
    graph = copy.deepcopy(draft_body.get("graph") or {})
    for node in graph.get("nodes") or []:
        data = node.get("data") or {}
        if data.get("type") == "tool":
            data["credential_id"] = credential_id
            node["data"] = data
    return {
        "graph": graph,
        "features": draft_body.get("features"),
        "hash": draft_body.get("hash"),
        "environment_variables": draft_body.get("environment_variables") or [],
        "conversation_variables": draft_body.get("conversation_variables") or [],
    }


def _build_draft_update_with_llm_model_credential(draft_body, credential_id):
    """在 graph.nodes 中 data.type == llm 的节点上为 model 写入 credential_id。"""
    graph = copy.deepcopy(draft_body.get("graph") or {})
    for node in graph.get("nodes") or []:
        data = node.get("data") or {}
        if data.get("type") == "llm":
            model = dict(data.get("model") or {})
            model["credential_id"] = credential_id
            data["model"] = model
            node["data"] = data
    return {
        "graph": graph,
        "features": draft_body.get("features"),
        "hash": draft_body.get("hash"),
        "environment_variables": draft_body.get("environment_variables") or [],
        "conversation_variables": draft_body.get("conversation_variables") or [],
    }


def _tongyi_provider_from_providers_body(body):
    """从 get_workspace_model_providers 的 JSON 中取出通义 provider 条目。"""
    for item in body.get("data") or []:
        if item.get("provider") == TONGYI_PROVIDER_PATH:
            return item
    return None


def _credential_row_by_id(provider_item, credential_id):
    """在 custom_configuration.available_credentials 中按 credential_id 查找。"""
    cc = (provider_item.get("custom_configuration") or {}).get("available_credentials") or []
    for row in cc:
        if row.get("credential_id") == credential_id:
            return row
    return None


@allure.epic("Dify Enterprise")
@allure.feature("Credential Management")
class TestE2ECase3P0:

    @pytest.mark.parametrize(
        "plugin_pre_installed",
        [{
            "plugin_id": "langgenius/github",
            "plugin_unique_identifier": "langgenius/github:0.3.2@1cb2f90ea05bbc7987fd712aff0a07594073816269125603dc2fa5b4229eb122",
            "source": "marketplace",
            "plugin_keyword": "github",
        }],
        indirect=True,
    )
    @allure.story("Create Tool Credential")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_tool_credential(self, admin_client, resource_tracker, plugin_pre_installed):
        """
        1. 企业后台凭据管理中创建tool凭据
        2. 将凭据分配给特定工作空间
        3、修改凭据名称
        4、修改凭据api-key为有效凭据
        5、修改凭据api-key为无效凭据
        """
        credential_svc = CredentialService()
        credential_name = random_name()
        plugin_res = plugin_pre_installed
        # Step 1: 创建凭据
        payload = {
            "pluginId": plugin_res["plugin_id"],
            "pluginName": plugin_res["pluginName"],
            "pluginIcon": plugin_res["pluginIcon"],
            "pluginVersion": plugin_res["pluginVersion"],
            "displayName": credential_name,
            "pluginArgs": {
                "access_tokens": TOOL_CREDENTIAL_KEY
            },
            "type": "CREDENTIAL_TYPE_PLUGIN",
        }
        with allure.step("Step1: 企业后台凭据管理中创建凭据"):
            log_step_data("create tool credential payload", **payload)
            create_resp = credential_svc.create_credential_success(client=admin_client, **payload,)
            credential_id = create_resp.get("id") or (create_resp.get("credential") or {}).get("id")
            assert credential_id, f"创建凭据响应中未返回 id: {create_resp}"
            resource_tracker.add_credential(credential_id=credential_id)
            log_resource_ids(credential_id=credential_id)
            log_step_result("create tool credential result", create_resp)

        # Step 2: 凭据分配给工作空间
        with allure.step("Step2: 凭据分配给工作空间（operate_credential_tenant_joins）"):
            operate_payload = {
                "isAll": False,
                "credentialId": credential_id,
                "batchDeleteIds": [],
                "batchCreateCredentialTenantJoins": [
                    {
                        "displayName": credential_name,
                        "allocatedTenant": ALLOCATED_TENANT_ID,
                        "credentialId": credential_id,
                    }
                ],
            }
            operate_resp = credential_svc.operate_credential_tenant_joins_success(
                client=admin_client,
                **operate_payload,
            )
            assert operate_resp is not None
            log_step_result("allocate tool credential result", operate_resp)

        # Step 3: 修改凭据名称
        with allure.step("Step3:修改凭据名称"):
            new_credential_name = random_name()
            update_payload = {
                "id": credential_id,
                "pluginId": plugin_res["plugin_id"],
                "pluginName": plugin_res["pluginName"],
                "pluginIcon": plugin_res["pluginIcon"],
                "pluginVersion": plugin_res["pluginVersion"],
                "displayName": new_credential_name,
                "pluginArgs": {
                    "access_tokens": TOOL_CREDENTIAL_KEY
                },
                "type": "CREDENTIAL_TYPE_PLUGIN"
            }
            res = credential_svc.update_credential_response(credential_id, client=admin_client, **update_payload)
            assert res.status_code == 200, f"修改凭据名称失败， status_code: {res.status_code}"
            data = res.json()
            assert data.get("displayName") == new_credential_name, f"修改凭据名称失败， credential_name: {data.get('displayName')}"

        # Step 3: 修改凭据access_token为合法的
        with allure.step("Step3:修改凭据api_key"):
            new_credential_name = random_name()
            update_payload = {
                "id": credential_id,
                "pluginId": plugin_res["plugin_id"],
                "pluginName": plugin_res["pluginName"],
                "pluginIcon": plugin_res["pluginIcon"],
                "pluginVersion": plugin_res["pluginVersion"],
                "displayName": new_credential_name,
                "pluginArgs": {
                    "access_tokens": NEW_TOOL_CREDENTIAL_KEY
                },
                "type": "CREDENTIAL_TYPE_PLUGIN"
            }
            res = credential_svc.update_credential_response(credential_id, client=admin_client, **update_payload)
            assert res.status_code == 200, f"修改凭据api_key失败， status_code: {res.status_code}"
            data = res.json()
            assert data.get("pluginArgs")["access_tokens"] == NEW_TOOL_CREDENTIAL_KEY, f"修改凭据api_key失败， credential_name: {data.get('pluginArgs').get('access_tokens')}"

            # Step 4: 修改凭据access_token为不合法的
            with allure.step("Step3:修改无效的凭据api_key"):
                invaild_credential_key = "ghp_8T0quox0dfretJ4RheBNWf0WcH3L490d3vkf"
                update_payload = {
                    "id": credential_id,
                    "pluginId": plugin_res["plugin_id"],
                    "pluginName": plugin_res["pluginName"],
                    "pluginIcon": plugin_res["pluginIcon"],
                    "pluginVersion": plugin_res["pluginVersion"],
                    "displayName": new_credential_name,
                    "pluginArgs": {
                        "access_tokens": invaild_credential_key
                    },
                    "type": "CREDENTIAL_TYPE_PLUGIN"
                }
                res = credential_svc.update_credential_response(credential_id, client=admin_client, **update_payload)
                assert res.status_code == 500, f"修改凭据api_key成功， status_code: {res.status_code}"
                data = res.json()
                assert data.get("message") == "Bad credentials", f"修改凭据api_key成功， credential_name: {data}"

    @allure.story("Create General Model Credential")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_model_general_credential(self, admin_client, resource_tracker, plugin_pre_installed):
        """
        1. 企业后台凭据管理中创建model凭据
        2. 将凭据分配给特定工作空间
        3、修改凭据名称
        4、修改凭据api-key为有效凭据
        5、修改凭据api-key为无效凭据
        """
        credential_svc = CredentialService()
        credential_name = random_name()
        plugin_res = plugin_pre_installed
        with allure.step("Step1: 创建通用模型凭据"):
            payload = {
                    "pluginId": plugin_res["plugin_id"],
                    "pluginName": plugin_res["pluginName"],
                    "pluginIcon": plugin_res["pluginIcon"],
                    "pluginVersion": plugin_res["pluginVersion"],
                    "displayName": credential_name,
                    "generalModel": GENERAL_MODEL_GENERAL,
                    "pluginArgs": {
                    "api_key": GENERAL_MODEL_CREDENTIAL_KEY
                    },
                    "type": "CREDENTIAL_TYPE_MODEL",
                    "customerModelType": ""
                    }
            res = credential_svc.create_credential_success(client=admin_client, **payload)
            credential_id = res.get("id") or (res.get("credential") or {}).get("id")
            assert credential_id, f"创建凭据响应中未返回 id: {res}"
            resource_tracker.add_credential(credential_id=credential_id)

        with allure.step("Step2: 修改模型凭据名称"):
            new_credential_name = random_name()
            update_payload = {
                "pluginId": plugin_res["plugin_id"],
                "pluginName": plugin_res["pluginName"],
                "pluginIcon": plugin_res["pluginIcon"],
                "pluginVersion": plugin_res["pluginVersion"],
                "displayName": new_credential_name,
                "generalModel": GENERAL_MODEL_GENERAL,
                "pluginArgs": {
                    "api_key": GENERAL_MODEL_CREDENTIAL_KEY
                },
                "type": "CREDENTIAL_TYPE_MODEL",
                "customerModelType": ""
            }
            res = credential_svc.update_credential_response(credential_id, client=admin_client, **update_payload)
            assert res.status_code == 200, f"修改凭据名称失败， status_code: {res.status_code}"
            data = res.json()
            assert data.get(
                "displayName") == new_credential_name, f"修改凭据名称失败， credential_name: {data.get('displayName')}"

        # Step 3: 修改凭据access_token为不合法的
        with allure.step("Step3:修改无效的凭据api_key"):
            invaild_credential_key = "jina_50c099b9091b4fksdfl403oopp20648fX_7F6HSZKccoA6ZZTaoRmYz81sq5"
            update_payload = {
                "id": credential_id,
                "pluginId": plugin_res["plugin_id"],
                "pluginName": plugin_res["pluginName"],
                "pluginIcon": plugin_res["pluginIcon"],
                "pluginVersion": plugin_res["pluginVersion"],
                "displayName": new_credential_name,
                "pluginArgs": {
                    "access_tokens": invaild_credential_key
                },
                "type": "CREDENTIAL_TYPE_PLUGIN"
            }
            res = credential_svc.update_credential_response(credential_id, client=admin_client, **update_payload)
            assert res.status_code == 500, f"修改凭据api_key成功， status_code: {res.status_code}"
            data = res.json()
            assert data.get("message") == "Credentials validation failed: 'api_key'", f"修改凭据api_key成功， credential_name: {data}"


    @pytest.mark.parametrize(
        "plugin_pre_installed",
        [{
            "plugin_id": "langgenius/openai",
            "plugin_unique_identifier": "langgenius/openai:0.2.8@aae2be0913b8c6f0b80cff58e08d7a8b4c214569b41778413fcaea204561ff16",
            "source": "marketplace",
            "plugin_keyword": "openai",
        }],
        indirect=True,
    )
    @allure.story("Create Customer Model Credential")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_model_customer_credential(self, admin_client, resource_tracker, plugin_pre_installed):
        """
        创建自定义模型凭据分配给特定工作空间
        """
        credential_svc = CredentialService()
        credential_name = random_name()
        plugin_res = plugin_pre_installed
        with allure.step("Step1: 创建自定义模型凭据"):
            payload = {
                "pluginId": plugin_res["plugin_id"] ,
                "pluginName": plugin_res["pluginName"],
                "pluginIcon": plugin_res["pluginIcon"],
                "pluginVersion": plugin_res["pluginVersion"],
                "displayName": credential_name,
                "generalModel": GENERAL_MODEL_CUSTOMER,
                "__model_type": "llm",
                "customerModelName": CUSTOMER_MODEL_NAME,
                "pluginArgs": {
                    "openai_api_key": CUSTOMER_MODEL_CREDENTIAL_KEY
                },
                "type": "CREDENTIAL_TYPE_MODEL",
                "customerModelType": "llm",
            }
            res = credential_svc.create_credential_success(client=admin_client, **payload)
            credential_id = res.get("id") or (res.get("credential") or {}).get("id")
            assert credential_id, f"创建自定义模型凭据响应中未返回 id: {res}"
            resource_tracker.add_credential(credential_id=credential_id)

    @pytest.mark.parametrize(
        "plugin_pre_installed",
        [{
            "plugin_id": "langgenius/github",
            "plugin_unique_identifier": "langgenius/github:0.3.2@1cb2f90ea05bbc7987fd712aff0a07594073816269125603dc2fa5b4229eb122",
            "source": "marketplace",
            "plugin_keyword": "github",
        }],
        indirect=True,
    )
    @allure.story("Allocate Tool Credential To All Workspaces")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_allocate_tool_credential_to_all_workspaces(self, admin_client, resource_tracker, plugin_pre_installed):
        """
        授权工具插件通用凭据给所有工作空间
        """
        credential_svc = CredentialService()
        credential_name = random_name()
        plugin_res = plugin_pre_installed

        with allure.step("Step1: 创建 github 通用凭据（工具类型）"):
            payload = {
                "pluginId": plugin_res.get("plugin_id") or "langgenius/github",
                "pluginName": plugin_res.get("pluginName") or "github",
                "pluginIcon": plugin_res.get("pluginIcon"),
                "pluginVersion": plugin_res.get("pluginVersion"),
                "displayName": credential_name,
                "pluginArgs": {"access_tokens": TOOL_CREDENTIAL_KEY},
                "type": "CREDENTIAL_TYPE_PLUGIN",
            }
            create_resp = credential_svc.create_credential_success(client=admin_client, **payload)
            credential_id = create_resp.get("id") or (create_resp.get("credential") or {}).get("id")
            assert credential_id, f"创建凭据响应中未返回 id: {create_resp}"
            resource_tracker.add_credential(credential_id=credential_id)

        with allure.step("Step2: 分配给所有工作空间（isAll=true），预期成功"):
            operate_payload = {
                "isAll": True,
                "credentialId": credential_id,
                "batchDeleteIds": [],
                "batchCreateCredentialTenantJoins": [],
            }
            operate_resp = credential_svc.operate_credential_tenant_joins_success(
                client=admin_client,
                **operate_payload,
            )
            assert operate_resp is not None, "分配凭据响应不应为空"
            assert operate_resp.get("message") == "success", f"预期 message=success，实际: {operate_resp}"

    @allure.story("Allocate Model Credential To All Workspaces")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_allocate_model_credential_to_all_workspaces(self, admin_client, resource_tracker, plugin_pre_installed):
        """
        分配模型凭据给所有工作空间：
        """
        credential_svc = CredentialService()
        credential_name = random_name()
        plugin_res = plugin_pre_installed

        with allure.step("Step1: 前置检查模型插件是否安装"):
            assert plugin_res.get("plugin_id"), "前置应有模型插件 plugin_id"

        with allure.step("Step2: 创建通用模型凭据"):
            payload = {
                "pluginId": plugin_res.get("plugin_id"),
                "pluginName": plugin_res.get("pluginName"),
                "pluginIcon": plugin_res.get("pluginIcon"),
                "pluginVersion": plugin_res.get("pluginVersion"),
                "displayName": credential_name,
                "generalModel": GENERAL_MODEL_GENERAL,
                "pluginArgs": {"api_key": GENERAL_MODEL_CREDENTIAL_KEY},
                "type": "CREDENTIAL_TYPE_MODEL",
                "customerModelType": "",
            }
            create_resp = credential_svc.create_credential_success(client=admin_client, **payload)
            credential_id = create_resp.get("id") or (create_resp.get("credential") or {}).get("id")
            assert credential_id, f"创建模型凭据响应中未返回 id: {create_resp}"
            resource_tracker.add_credential(credential_id=credential_id)

        with allure.step("Step3: 分配给所有工作空间（isAll=true），预期成功"):
            operate_payload = {
                "isAll": True,
                "credentialId": credential_id,
                "batchDeleteIds": [],
                "batchCreateCredentialTenantJoins": [],
            }
            operate_resp = credential_svc.operate_credential_tenant_joins_success(
                client=admin_client,
                **operate_payload,
            )
            assert operate_resp is not None, "分配凭据响应不应为空"
            assert operate_resp.get("message") == "success", f"预期 message=success，实际: {operate_resp}"

    @allure.story("Tool Credential Policy Change")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tool_plugin_credential_policy_change(
        self,
        credential_tools_policy__all_allowed,
        import_app_fixture,
        resource_tracker,
        console_client,
        admin_client,
    ):
        """
        工具插件凭据策略变更：
        1. 工作空间创建自定义工具凭据
        2、修改自定义凭据策略为禁用
        3. 自定义凭据不可用
        """
        _ = credential_tools_policy__all_allowed
        app_id = import_app_fixture
        console_svc = ConsoleService()
        apps_svc = AppsService()
        credential_svc = CredentialService()

        with allure.step("Step1: 工作空间添加自定义工具凭据"):
            credential_name = random_name()
            add_payload = {
                "credentials": {"access_tokens": TOOL_CREDENTIAL_KEY},
                "type": "api-key",
                "name": credential_name,
            }
            log_step_data("add builtin tool credential payload", **add_payload)
            add_data = console_svc.add_workspace_builtin_tool_credential_success(console_client, **add_payload)
            assert add_data.get("result") == "success", f"预期 result=success: {add_data}"

            info = console_svc.get_workspace_builtin_tool_credential_info_success(console_client)
            creds = info.get("credentials") or []
            matched = next((c for c in creds if c.get("name") == credential_name), None)
            assert matched is not None, f"凭据列表中未找到 {credential_name}: {creds}"
            ws_credential_id = matched.get("id")
            assert ws_credential_id, f"凭据缺少 id: {matched}"
            resource_tracker.add_builtin_tool_credential(credential_id=ws_credential_id)
            log_resource_ids(workspace_credential_id=ws_credential_id, app_id=app_id)
            log_step_result("builtin tool credential info", info)

        with allure.step("Step4: 更新 workflow draft，为 tool 节点绑定 credential_id"):
            draft_body = apps_svc.get_workflow_draft_success(app_id, console_client)
            updated_draft = _build_draft_update_with_tool_credential(draft_body, ws_credential_id)
            apps_svc.update_workflow_draft_success(app_id, console_client, **updated_draft)
            log_step_result("updated workflow draft", updated_draft)

        with allure.step("Step5: 凭据策略检查，items 中应包含创建的 credentialId"):
            check_payload = {
                "type": "CREDENTIAL_TYPE_PLUGIN",
                "allowToolsUseCustomToken": True,
                "exceptToolPlugins": ["langgenius/github"],
                "allowModelsUseCustomToken": False,
                "exceptModelPlugins": [],
            }
            check_res = credential_svc.check_credential_policy_response(client=admin_client, **check_payload)
            assert check_res.status_code == 200, f"check_credential_policy 失败: {check_res.status_code}, {check_res.text[:300]}"
            check_data = check_res.json() or {}
            items = check_data.get("items") or []
            found_ids = {it.get("credentialId") for it in items if isinstance(it, dict)}
            assert ws_credential_id in found_ids, (
                f"检查项中应包含凭据 {ws_credential_id}, found={found_ids}, items={items}"
            )
            log_step_result("check credential policy result", check_data)

        with allure.step("Step6: 策略限制修改为禁止github配置自定义凭据"):
            credential_payload = {
                "type": "CREDENTIAL_TYPE_PLUGIN",
                "allowToolsUseCustomToken": True,
                "exceptToolPlugins": ["langgenius/github"],
                "allowModelsUseCustomToken": False,
                "exceptModelPlugins": [],
            }
            res = credential_svc.update_credential_policy_response(client=admin_client, **credential_payload)
            assert res.status_code == 200, f"update_credential_policy 失败: {res.status_code}, {res.text[:300]}"


        with allure.step("Step7: 策略限制下查询凭据，返回信息中自定义凭据不可使用"):
            info = console_svc.get_workspace_builtin_tool_credential_info_success(console_client)
            creds = info.get("credentials") or []
            matched = next((c for c in creds if c.get("name") == credential_name), None)
            assert matched is not None, f"凭据列表中未找到 {credential_name}: {creds}"
            credential_status = matched.get("not_allowed_to_use")
            assert credential_status == True, f"凭据处于可用状态 id: {credential_status}"


    @allure.story("Model Credential Policy Change")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "plugin_pre_installed",
        [{
            "plugin_id": "langgenius/tongyi",
            "plugin_unique_identifier": "langgenius/tongyi:0.1.32@20a5454088fa017b72490e1cbaeebff21094d11b13e41197591734d1c08cdbb5",
            "source": "marketplace",
            "plugin_keyword": "tongyi",
        }],
        indirect=True,
    )
    def test_model_plugin_credential_policy_change(
        self,
        credential_model_policy__all_allowed,
        plugin_pre_installed,
        import_model_app_fixture,
        resource_tracker,
        console_client,
        admin_client,
    ):
        """
        模型插件凭据策略变更：
        前置：导入通义工作流应用；企业策略为「模型允许使用自定义 token」（全允许）。
        1. 工作空间创建通义自定义模型凭据
        2. 查询 model-providers，若当前生效凭据非本凭据则 switch
        3. 更新 workflow draft，为 LLM 节点绑定 credential_id
        4. 修改企业凭据策略为禁止通义使用自定义凭据（exceptModelPlugins）
        5. check 接口校验仍统计到当前使用的凭据
        6. 查询 model-providers，对应 credential_id 的 not_allowed_to_use 为 True
        """
        _ = credential_model_policy__all_allowed
        _ = plugin_pre_installed
        app_id = import_model_app_fixture
        credential_name = random_name()
        console_svc = ConsoleService()
        credential_svc = CredentialService()

        with allure.step("Step1: 工作空间添加通义自定义模型凭据"):
            add_payload = {
                "credentials": {
                    "dashscope_api_key": DASHSCOPE_SECRET,
                    "use_international_endpoint": "false",
                },
                "name": credential_name,
            }
            log_step_data("add model credential payload", **add_payload)
            add_data = console_svc.add_workspace_model_provider_credential_success(
                console_client, provider_path=TONGYI_PROVIDER_PATH, **add_payload
            )
            assert add_data.get("result") == "success", f"预期 result=success: {add_data}"

            prov_body = console_svc.get_workspace_model_providers_success(console_client)
            tongyi_item = _tongyi_provider_from_providers_body(prov_body)
            assert tongyi_item is not None, f"未找到 provider {TONGYI_PROVIDER_PATH}: {prov_body}"
            ws_credential_id = None
            for row in (tongyi_item.get("custom_configuration") or {}).get("available_credentials") or []:
                if row.get("credential_name") == credential_name:
                    ws_credential_id = row.get("credential_id")
                    break
            assert ws_credential_id, (
                f"凭据列表中未找到名称 {credential_name}: "
                f"{tongyi_item.get('custom_configuration')}"
            )
            resource_tracker.add_workspace_model_credential(
                ws_credential_id, provider_path=TONGYI_PROVIDER_PATH
            )
            log_resource_ids(model_workspace_credential_id=ws_credential_id, app_id=app_id)
            log_step_result("model providers after add credential", prov_body)

        with allure.step("Step2: 若当前生效凭据非本凭据则切换"):
            tongyi_item = _tongyi_provider_from_providers_body(
                console_svc.get_workspace_model_providers_success(console_client)
            )
            current_id = (tongyi_item.get("custom_configuration") or {}).get("current_credential_id")
            if current_id != ws_credential_id:
                sw = console_svc.switch_workspace_model_provider_credential_success(
                    ws_credential_id,
                    client=console_client,
                    provider_path=TONGYI_PROVIDER_PATH,
                )
                assert sw.get("result") == "success", sw

        # with allure.step("Step3: 更新 workflow draft，使应用在用的 LLM 绑定本凭据"):
        #     draft_res = get_workflow_draft(console_client, app_id)
        #     assert draft_res.status_code == 200, draft_res.text[:300]
        #     draft_body = draft_res.json() if draft_res.text else {}
        #     updated = _build_draft_update_with_llm_model_credential(draft_body, ws_credential_id)
        #     up_res = update_workflow_draft(console_client, app_id, **updated)
        #     assert up_res.status_code == 200, f"更新 draft 失败: {up_res.status_code}, {up_res.text[:300]}"

        with allure.step("Step4: 修改企业凭据策略为不允许此模型（exceptModelPlugins）"):
            credential_payload = {
                "type": "CREDENTIAL_TYPE_MODEL",
                "allowToolsUseCustomToken": False,
                "exceptToolPlugins": [],
                "allowModelsUseCustomToken": True,
                "exceptModelPlugins": [TONGYI_PROVIDER_PATH],
            }
            res = credential_svc.update_credential_policy_response(client=admin_client, **credential_payload)
            assert res.status_code == 200, f"update_credential_policy 失败: {res.status_code}, {res.text[:300]}"

        with allure.step("Step5: check 接口校验：当前在使用的凭据仍出现在 items 中"):
            check_payload = {
                "type": "CREDENTIAL_TYPE_MODEL",
                "allowToolsUseCustomToken": False,
                "exceptToolPlugins": [],
                "allowModelsUseCustomToken": True,
                "exceptModelPlugins": [TONGYI_PROVIDER_PATH],
            }
            check_res = credential_svc.check_credential_policy_response(client=admin_client, **check_payload)
            assert check_res.status_code == 200, (
                f"check_credential_policy 失败: {check_res.status_code}, {check_res.text[:300]}"
            )
            check_data = check_res.json() or {}
            items = check_data.get("items") or []
            found_ids = {it.get("credentialId") for it in items if isinstance(it, dict)}
            assert ws_credential_id in found_ids, (
                f"检查项中应包含凭据 {ws_credential_id}, found={found_ids}, items={items}"
            )
            log_step_result("model credential policy check result", check_data)

        with allure.step("Step6: GET model-providers：过滤 credential_id，not_allowed_to_use 为 True"):
            tongyi_item = _tongyi_provider_from_providers_body(
                console_svc.get_workspace_model_providers_success(console_client)
            )
            assert tongyi_item is not None
            row = _credential_row_by_id(tongyi_item, ws_credential_id)
            assert row is not None, (
                f"available_credentials 中未找到 {ws_credential_id}: "
                f"{tongyi_item.get('custom_configuration')}"
            )
            assert row.get("not_allowed_to_use") is True, (
                f"预期 not_allowed_to_use=True，实际: {row}"
            )
