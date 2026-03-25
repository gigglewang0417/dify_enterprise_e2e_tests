import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import allure
import pytest

from api.member_api import MEMBER_BASE_PATH, create_member, get_member, list_members, update_member
from common.client import Client
from services.auth_service import AuthService
from utils.random_util import random_email, random_name
from utils.test_log import log_resource_ids, log_step_data, log_step_result

CREATE_MEMBER_PERF_THRESHOLD_SECONDS = 8.0
CONCURRENCY_WORKERS = 5


def _build_member_payload(email=None, name=None, status="active", **extra):
    payload = {
        "email": email if email is not None else random_email(),
        "name": name if name is not None else random_name(),
        "status": status,
    }
    payload.update(extra)
    return payload


def _extract_member_id(data):
    return data.get("id") or (data.get("account") or {}).get("id")


def _extract_member_status(data):
    member = data.get("member") or data
    account = member.get("account") or {}
    return member.get("status") or account.get("status")


def _find_member_by_email(list_body, email):
    for row in list_body.get("data") or []:
        account = row.get("account") or {}
        if account.get("email") == email:
            return row
    return None


def _assert_validation_error(response):
    assert response.status_code in (400, 404, 409, 415, 422, 500), (
        f"预期参数校验类错误，实际: {response.status_code}, {response.text[:300]}"
    )


def _assert_auth_error(response):
    assert response.status_code in (401, 403), (
        f"预期鉴权失败，实际: {response.status_code}, {response.text[:300]}"
    )


@allure.epic("Dify Enterprise")
@allure.feature("Member API")
@pytest.mark.integration
class TestCreateMemberAPI:

    @allure.story("Create Member Happy Path")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_member_happy_path(self, admin_client, resource_tracker):
        payload = _build_member_payload()
        with allure.step("创建成员并校验返回成功"):
            log_step_data("create member happy path payload", **payload)
            res = create_member(admin_client, **payload)
            assert res.status_code == 200, f"创建成员失败: {res.status_code}, {res.text[:300]}"
            data = res.json() if res.text else {}
            member_id = _extract_member_id(data)
            assert member_id, f"响应中未返回 member_id: {data}"
            resource_tracker.add_member(member_id)
            log_resource_ids(member_id=member_id)
            log_step_result("create member happy path result", data)

        with allure.step("查询成员列表，确认新成员可见"):
            list_body = list_members(admin_client, email=payload["email"]).json()
            member_row = _find_member_by_email(list_body, payload["email"])
            assert member_row is not None, f"成员列表中未找到新成员: {list_body}"

    @allure.story("Missing Required Parameters")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "payload",
        [
            {"name": random_name(), "status": "active"},
            {"email": random_email(), "status": "active"},
            {"email": random_email(), "name": random_name()},
            {},
        ],
    )
    def test_create_member_missing_required_fields(self, admin_client, payload):
        log_step_data("create member missing required payload", **payload)
        res = create_member(admin_client, **payload)
        _assert_validation_error(res)
        log_step_result("missing required response", res.json() if res.text else {})

    @allure.story("Invalid Parameter Format")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "payload",
        [
            {"email": "not-an-email", "name": random_name(), "status": "active"},
            {"email": "中文邮箱", "name": random_name(), "status": "active"},
            # {"email": random_email(), "name": "", "status": "active"},
        ],
    )
    def test_create_member_invalid_format(self, admin_client, payload):
        log_step_data("create member invalid format payload", **payload)
        res = create_member(admin_client, **payload)
        _assert_validation_error(res)
        log_step_result("invalid format response", res.json() if res.text else {})

    @allure.story("Boundary Values")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_boundary_values(self, admin_client, resource_tracker):
        valid_payload = _build_member_payload(name="A")
        invalid_payload = _build_member_payload(
            email=f"{'a' * 80}@example.com",
            name="N" * 256,
        )

        with allure.step("校验最小边界值可以成功创建"):
            log_step_data("boundary valid payload", **valid_payload)
            res = create_member(admin_client, **valid_payload)
            assert res.status_code == 200, f"最小边界创建失败: {res.status_code}, {res.text[:300]}"
            data = res.json() if res.text else {}
            member_id = _extract_member_id(data)
            assert member_id, f"最小边界响应缺少 member_id: {data}"
            resource_tracker.add_member(member_id)
            log_resource_ids(boundary_member_id=member_id)

        with allure.step("校验超长边界值被拒绝"):
            log_step_data("boundary invalid payload", **invalid_payload)
            res = create_member(admin_client, **invalid_payload)
            _assert_validation_error(res)
            log_step_result("boundary invalid response", res.json() if res.text else {})

    @allure.story("Invalid Parameter Types")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "payload",
        [
            {"email": 12345, "name": random_name(), "status": "active"},
            {"email": random_email(), "name": ["bad-type"], "status": "active"},
            {"email": random_email(), "name": random_name(), "status": 1},
            {"email": {"email": random_email()}, "name": random_name(), "status": "active"},
        ],
    )
    def test_create_member_invalid_types(self, admin_client, payload):
        log_step_data("create member invalid types payload", **payload)
        res = create_member(admin_client, **payload)
        _assert_validation_error(res)
        log_step_result("invalid types response", res.json() if res.text else {})

    @allure.story("Extra Parameters")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_member_with_extra_fields(self, admin_client, resource_tracker):
        payload = _build_member_payload(unexpected_field="should-not-break", role="admin")
        log_step_data("create member extra fields payload", **payload)
        res = create_member(admin_client, **payload)
        assert res.status_code in (200, 400, 422), (
            f"多余参数场景不应返回异常状态: {res.status_code}, {res.text[:300]}"
        )
        data = res.json() if res.text else {}
        log_step_result("extra fields response", data)
        if res.status_code == 200:
            member_id = _extract_member_id(data)
            assert member_id, f"成功创建时应返回 member_id: {data}"
            resource_tracker.add_member(member_id)
            assert "unexpected_field" not in data, f"多余参数不应直接持久化到响应: {data}"

    @allure.story("Permission Checks")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_permission_checks(self, console_client):
        payload = _build_member_payload()

        with allure.step("未登录请求应被拒绝"):
            anonymous_client = Client()
            res = create_member(anonymous_client, **payload)
            _assert_auth_error(res)
            log_step_result("anonymous create member response", res.json() if res.text else {})

        with allure.step("越权请求应被拒绝"):
            res = create_member(console_client, **payload)
            _assert_auth_error(res)
            log_step_result("console client create member response", res.json() if res.text else {})

    @allure.story("Business State Transition")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_business_status_flow(self, admin_client, resource_tracker):
        payload = _build_member_payload(status="active")
        create_res = create_member(admin_client, **payload)
        assert create_res.status_code == 200, f"创建成员失败: {create_res.status_code}, {create_res.text[:300]}"
        create_data = create_res.json() if create_res.text else {}
        member_id = _extract_member_id(create_data)
        assert member_id, f"创建成员响应缺少 member_id: {create_data}"
        resource_tracker.add_member(member_id)
        log_resource_ids(member_id=member_id)

        with allure.step("从 active -> banned -> active 完成状态流转"):
            banned_res = update_member(
                admin_client,
                member_id,
                id=member_id,
                email=payload["email"],
                name=payload["name"],
                status="banned",
            )
            assert banned_res.status_code == 200, f"禁用成员失败: {banned_res.status_code}, {banned_res.text[:300]}"

            active_res = update_member(
                admin_client,
                member_id,
                id=member_id,
                email=payload["email"],
                name=payload["name"],
                status="active",
            )
            assert active_res.status_code == 200, f"重新启用成员失败: {active_res.status_code}, {active_res.text[:300]}"

            detail = get_member(admin_client, member_id).json()
            account = detail["account"]
            returned_id = _extract_member_id(account)
            assert returned_id == member_id, f"状态流转后成员详情异常: {detail}"
            log_step_result("member state transition detail", detail)

    @allure.story("Idempotency")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_idempotency(self, admin_client, resource_tracker):
        payload = _build_member_payload()
        log_step_data("idempotency payload", **payload)

        first_res = create_member(admin_client, **payload)
        assert first_res.status_code == 200, f"首次创建失败: {first_res.status_code}, {first_res.text[:300]}"
        first_data = first_res.json() if first_res.text else {}
        member_id = _extract_member_id(first_data)
        assert member_id, f"首次创建响应缺少 member_id: {first_data}"
        resource_tracker.add_member(member_id)

        second_res = create_member(admin_client, **payload)
        assert second_res.status_code in (400, 409), (
            f"重复创建应冲突或被拒绝: {second_res.status_code}, {second_res.text[:300]}"
        )
        log_resource_ids(member_id=member_id)
        log_step_result("idempotency first response", first_data)
        log_step_result("idempotency second response", second_res.json() if second_res.text else {})

    @allure.story("Concurrency")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_concurrent_requests(self, resource_tracker):
        payloads = [_build_member_payload() for _ in range(CONCURRENCY_WORKERS)]

        def create_once(payload):
            client, _ = AuthService.admin_login()
            start = time.perf_counter()
            res = create_member(client, **payload)
            elapsed = time.perf_counter() - start
            body = res.json() if res.text else {}
            return payload, res.status_code, body, elapsed

        with allure.step("并发创建不同成员，验证成功率与响应稳定性"):
            futures = []
            with ThreadPoolExecutor(max_workers=CONCURRENCY_WORKERS) as executor:
                for payload in payloads:
                    futures.append(executor.submit(create_once, payload))

            results = [future.result() for future in as_completed(futures)]
            success_ids = []
            for payload, status_code, body, elapsed in results:
                assert status_code == 200, f"并发创建失败: status={status_code}, body={body}"
                member_id = _extract_member_id(body)
                assert member_id, f"并发创建响应缺少 member_id: {body}"
                success_ids.append(member_id)
                resource_tracker.add_member(member_id)
                assert elapsed < CREATE_MEMBER_PERF_THRESHOLD_SECONDS, (
                    f"并发创建单请求过慢: {elapsed:.3f}s, payload={payload}"
                )
            assert len(success_ids) == CONCURRENCY_WORKERS, f"并发创建成功数不足: {success_ids}"
            log_step_result("concurrent create results", results)

    @allure.story("Performance")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_member_response_time(self, admin_client, resource_tracker):
        payload = _build_member_payload()
        log_step_data("performance payload", **payload)
        start = time.perf_counter()
        res = create_member(admin_client, **payload)
        elapsed = time.perf_counter() - start
        assert res.status_code == 200, f"性能用例创建失败: {res.status_code}, {res.text[:300]}"
        data = res.json() if res.text else {}
        member_id = _extract_member_id(data)
        assert member_id, f"性能用例响应缺少 member_id: {data}"
        resource_tracker.add_member(member_id)
        assert elapsed < CREATE_MEMBER_PERF_THRESHOLD_SECONDS, (
            f"create_member 响应时间超阈值: {elapsed:.3f}s > {CREATE_MEMBER_PERF_THRESHOLD_SECONDS}s"
        )
        log_resource_ids(member_id=member_id)
        log_step_result("performance result", {"elapsed_seconds": elapsed, "body": data})

    @allure.story("Exception Handling")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_invalid_json_body(self, admin_client):
        with allure.step("发送非法 JSON，接口应返回可预期错误而非 500"):
            res = admin_client.post(
                MEMBER_BASE_PATH,
                data='{"email": "bad-json",',
                headers={"Content-Type": "application/json"},
            )
            assert res.status_code in (400, 415, 422), (
                f"非法 JSON 不应触发 500: {res.status_code}, {res.text[:300]}"
            )
            log_step_result("invalid json response", res.text[:500])

    @allure.story("Data Consistency")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_data_consistency(self, admin_client, resource_tracker):
        payload = _build_member_payload()
        create_res = create_member(admin_client, **payload)
        assert create_res.status_code == 200, f"创建成员失败: {create_res.status_code}, {create_res.text[:300]}"
        create_data = create_res.json() if create_res.text else {}
        member_id = _extract_member_id(create_data)
        assert member_id, f"响应缺少 member_id: {create_data}"
        resource_tracker.add_member(member_id)

        with allure.step("查询成员详情与列表，校验关键字段一致"):
            detail_data = get_member(admin_client, member_id).json()
            list_data = list_members(admin_client, email=payload["email"]).json()
            member_row = _find_member_by_email(list_data, payload["email"])

            assert _extract_member_id(detail_data) == member_id, f"详情中的成员 ID 不一致: {detail_data}"
            assert member_row is not None, f"列表中未找到创建成员: {list_data}"
            account = member_row.get("account") or {}
            assert account.get("email") == payload["email"], f"列表中的 email 不一致: {member_row}"
            assert account.get("name") == payload["name"], f"列表中的 name 不一致: {member_row}"
            log_resource_ids(member_id=member_id)
            log_step_result(
                "data consistency result",
                {"create": create_data, "detail": detail_data, "list_match": member_row},
            )
