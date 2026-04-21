"""
插件管理
E2E P0：安装插件 -> 轮询安装任务直至成功 -> 将插件分配给工作空间
"""
import allure

from services.console_service import ConsoleService
from services.plugin_service import PluginService
from utils.test_log import log_resource_ids, log_step_data, log_step_result

# 安装插件配置
TOOL_PLUGIN_UNIQUE_IDENTIFIER = "langgenius/github:0.3.1@d11d1199e99933a27fc210a3cb5579addb51a97e80b9f26dfb165eac6a6eadf5"
MODEL_PLUGIN_UNIQUE_IDENTIFIER = "langgenius/tongyi:0.1.28@ad074894f4aac6840ef8fb68dbfcf51d13c7800450757a8d99bacbefd245a6ab"

#工作空间配置
TENANT_IDS = ["f0435a59-fc6b-4d40-a478-6a53d00bb922"]

# 轮询配置
INSTALL_TASK_POLL_INTERVAL_SEC = 3
INSTALL_TASK_TIMEOUT_SEC = 80
INSTALL_TASK_STATUS_SUCCESS = ("success", "completed", "succeeded")
INSTALL_TASK_STATUS_FAILED = ("failed", "error")



@allure.epic("Dify Enterprise")
@allure.feature("Plugin Management")
class TestE2ECase4P0:

    @allure.story("Install Tool Plugin And Apply To Workspace")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_install_tool_plugin(self, admin_client, console_client, resource_tracker):
        """
        1. 企业后台安装 github 0.3.1 插件，从 response 拿到 taskId，轮询 list_plugin_install_tasks 查任务 status 直至成功或 60s 超时
        2. 调用 apply_plugin 将插件分配给工作空间
        """
        # Step 1: 安装插件，获取 taskId
        with allure.step("Step1: 企业后台安装 github 0.3.1 插件"):
            plugin_svc = PluginService()
            console_svc = ConsoleService()
            plugin_id = "langgenius/github"
            install_plugin_payload = {
                "pluginUniqueIdentifier": TOOL_PLUGIN_UNIQUE_IDENTIFIER,
                "source": "marketplace",
            }
            log_step_data("install plugin payload", **install_plugin_payload)
            body = plugin_svc.install_plugin_success(
                client=admin_client,
                **install_plugin_payload,
            )
            task_id = body.get("task_id")
            assert task_id, f"安装插件响应中未返回 task_id/taskIds: {body}"
            log_resource_ids(plugin_install_task_id=task_id)
            log_step_result("install plugin result", body)

        # 轮询任务状态，超时 60s（使用 utils.polling.wait_until）
        with allure.step("轮询安装任务状态直至成功或超时"):
            try:
                plugin_svc.wait_for_install_task_success(
                    task_id,
                    client=admin_client,
                    timeout=INSTALL_TASK_TIMEOUT_SEC,
                    interval=INSTALL_TASK_POLL_INTERVAL_SEC,
                )
            except TimeoutError as e:
                raise AssertionError(
                    f"安装任务未在 {INSTALL_TASK_TIMEOUT_SEC}s 内完成, taskId={task_id}"
                ) from e
             # 登记插件卸载 payload，cleanup 时会调用 uninstall_plugin_success(client, **payload)。
            uninstall_plugin_payload = {
                "pluginUniqueIdentifier": TOOL_PLUGIN_UNIQUE_IDENTIFIER
            }
            resource_tracker.add_plugin(**uninstall_plugin_payload)

        # Step 2: 插件分配给工作空间
        with allure.step("Step2: 安装的插件分配给工作空间（apply_plugin）"):
            apply_plugin_payload = {
                "pluginUniqueIdentifier": TOOL_PLUGIN_UNIQUE_IDENTIFIER,
                "tenantIds": TENANT_IDS,
            }
            log_step_data("apply plugin payload", **apply_plugin_payload)
            apply_res = plugin_svc.apply_plugin_success(client=admin_client, **apply_plugin_payload)
            assert apply_res is not None, "apply_plugin 响应不应为空"
            log_step_result("apply plugin result", apply_res)

        with allure.step("Step3: Console 查询当前工作空间插件安装实例（installations/ids）"):
            log_step_data("list installations by plugin ids", plugin_ids=plugin_id)
            install_data = console_svc.list_workspace_plugin_installations_ids_success(
                client=console_client,
                plugin_ids=plugin_id,
            )
            plugins = install_data.get("plugins") or []
            entry = next(
                (p for p in plugins if isinstance(p, dict) and p.get("plugin_id") == plugin_id),
                None,
            )
            assert entry is not None, (
                f"plugins 中应有 plugin_id={plugin_id!r} 的安装记录, 实际: {plugins}"
            )
            actual_uid = entry.get("plugin_unique_identifier")
            assert actual_uid == TOOL_PLUGIN_UNIQUE_IDENTIFIER, (
                f"plugin_unique_identifier 应与安装使用的 MODEL_PLUGIN_UNIQUE_IDENTIFIER 一致: "
                f"期望 {MODEL_PLUGIN_UNIQUE_IDENTIFIER!r}, 实际 {actual_uid!r}"
            )
            log_step_result("list plugin installations result", install_data)

    @allure.story("Install Model Plugin, Apply To Workspace, Query Latest Version In Console")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_install_model_plugin(self, admin_client, console_client, resource_tracker):
        """
        1. 企业后台安装 tongyi 模型插件，从 response 取 taskId，轮询安装任务直至成功或超时
        2. apply_plugin 将插件分配给指定工作空间
        3. 使用 Console 登录态调用 list_workspace_plugin_latest_versions，校验 langgenius/tongyi 版本信息
        """
        plugin_svc = PluginService()
        console_svc = ConsoleService()
        tongyi_plugin_id = "langgenius/tongyi"

        # Step 1: 安装插件
        with allure.step("Step1: 企业后台安装 tongyi 模型插件（marketplace）"):
            install_plugin_payload = {
                "pluginUniqueIdentifier": MODEL_PLUGIN_UNIQUE_IDENTIFIER,
                "source": "marketplace",
            }
            log_step_data("install plugin payload", **install_plugin_payload)
            body = plugin_svc.install_plugin_success(
                client=admin_client,
                **install_plugin_payload,
            )
            task_id = body.get("task_id")
            assert task_id, f"安装插件响应中未返回 task_id/taskIds: {body}"
            log_resource_ids(plugin_install_task_id=task_id)
            log_step_result("install plugin result", body)

        with allure.step("轮询安装任务状态直至成功或超时"):
            try:
                plugin_svc.wait_for_install_task_success(
                    task_id,
                    client=admin_client,
                    timeout=INSTALL_TASK_TIMEOUT_SEC,
                    interval=INSTALL_TASK_POLL_INTERVAL_SEC,
                )
            except TimeoutError as e:
                raise AssertionError(
                    f"安装任务未在 {INSTALL_TASK_TIMEOUT_SEC}s 内完成, taskId={task_id}"
                ) from e
            uninstall_plugin_payload = {
                "pluginUniqueIdentifier": MODEL_PLUGIN_UNIQUE_IDENTIFIER,
            }
            resource_tracker.add_plugin(**uninstall_plugin_payload)

        with allure.step("Step2: 将插件分配给工作空间（apply_plugin）"):
            apply_plugin_payload = {
                "pluginUniqueIdentifier": MODEL_PLUGIN_UNIQUE_IDENTIFIER,
                "tenantIds": TENANT_IDS,
            }
            log_step_data("apply plugin payload", **apply_plugin_payload)
            apply_res = plugin_svc.apply_plugin_success(client=admin_client, **apply_plugin_payload)
            assert apply_res is not None, "apply_plugin 响应不应为空"
            log_step_result("apply plugin result", apply_res)

        with allure.step("Step3: Console 查询当前工作空间插件安装实例（installations/ids）"):
            log_step_data("list installations by plugin ids", plugin_ids=tongyi_plugin_id)
            install_data = console_svc.list_workspace_plugin_installations_ids_success(
                client=console_client,
                plugin_ids=tongyi_plugin_id,
            )
            plugins = install_data.get("plugins") or []
            entry = next(
                (p for p in plugins if isinstance(p, dict) and p.get("plugin_id") == tongyi_plugin_id),
                None,
            )
            assert entry is not None, (
                f"plugins 中应有 plugin_id={tongyi_plugin_id!r} 的安装记录, 实际: {plugins}"
            )
            actual_uid = entry.get("plugin_unique_identifier")
            assert actual_uid == MODEL_PLUGIN_UNIQUE_IDENTIFIER, (
                f"plugin_unique_identifier 应与安装使用的 MODEL_PLUGIN_UNIQUE_IDENTIFIER 一致: "
                f"期望 {MODEL_PLUGIN_UNIQUE_IDENTIFIER!r}, 实际 {actual_uid!r}"
            )
            log_step_result("list plugin installations result", install_data)

