"""
ADMIN API
E2E P0：企业后台创建 secret key -> 使用 secret key 调用 Admin API 获取工作空间列表
"""
import os

import allure

from services.admin_service import AdminService
from services.secretkey_service import SecretKeyService
from utils.test_log import log_resource_ids, log_step_data, log_step_result

# Admin API 端点（可从环境变量 ADMIN_API_BASE_URL 覆盖）
ADMIN_API_BASE_URL = os.getenv("ADMIN_API_BASE_URL", "https://enterprise-platform.dify.dev/admin-api/v1")


@allure.epic("Dify Enterprise")
@allure.feature("Admin API")
class TestE2ECase5P0:

    @allure.story("Secret Key Lists Workspaces")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_admin_secret_key_list_workspaces(self, admin_client, resource_tracker):
        """
        1. 企业后台创建 secret key，从 response 获取 secretKey
        2. 使用 secretKey 调用 Admin API GET /workspaces，断言状态码 200 且 response 不为空
        """
        # Step 1: 企业后台创建 secret key
        with allure.step("Step1: 企业后台创建 secret key"):
            secret_svc = SecretKeyService()
            log_step_data("create secret key payload", name="auto_test")
            body = secret_svc.create_secret_key_success(client=admin_client)
            secret_key = body.get("secretKey")
            assert secret_key, f"创建 secret key 响应中未返回 secretKey: {body}"
            secret_key_id = body.get("id")
            resource_tracker.add_secert_key(secret_key_id)
            log_resource_ids(secret_key_id=secret_key_id)
            log_step_result("create secret key result", body)

        # Step 2: 使用 secret key 调用 Admin API 获取工作空间列表
        with allure.step("Step2: 使用 secret key 调用 Admin API 获取工作空间列表"):
            log_step_data("admin api list workspaces params", base_url=ADMIN_API_BASE_URL, page=1, limit=10)
            data = AdminService.list_workspaces_success(
                secret_key,
                base_url=ADMIN_API_BASE_URL,
                page=1,
                limit=10,
            )
            assert data is not None, "response 解析为空"
            log_step_result("admin api workspaces", data)
