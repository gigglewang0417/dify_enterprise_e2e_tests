"""
审计日志
E2E P0：创建成员 -> 查询审计日志中该成员的创建记录
"""
from datetime import datetime, timezone

import allure
import time
from services.audit_service import AuditService
from services.member_service import MemberService
from utils.test_log import log_resource_ids, log_step_data, log_step_result
from utils.random_util import random_email

MEMBER_EMAIL = random_email()
MEMBER_NAME = "auto_test"

RESOURCE_TYPE_MEMBER = "RESOURCE_TYPE_MEMBER"
OPERATION_TYPE_CREATE = "OPERATION_TYPE_CREATE"
CURSOR_DIRECTION_NEXT = "CURSOR_DIRECTION_NEXT"


def _today_start_end_utc():
    """返回当天 0 时与 24 时（23:59:59.999）的 UTC ISO 字符串，用于审计日志时间范围。"""
    now = datetime.now(timezone.utc)
    today = now.date()
    start_time = f"{today.isoformat()}T00:00:00.000Z"
    end_time = f"{today.isoformat()}T23:59:59.999Z"
    return start_time, end_time


@allure.epic("Dify Enterprise")
@allure.feature("Audit Log")
class TestE2ECase6P0:

    @allure.story("Create Member Audit Event Query")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_member_audit_log_query(self, admin_client, resource_tracker):
        """
        1. 企业后台创建成员（email=auto_test@dify.ai, name=auto_test）
        2. 查询审计日志：resourceType=RESOURCE_TYPE_MEMBER、operationType=OPERATION_TYPE_CREATE，
           时间范围为当天 0 时～24 时，断言能查到创建该成员的日志
        """
        # Step 1: 企业后台创建成员
        with allure.step("Step1: 企业后台创建成员"):
            member_svc = MemberService()
            log_step_data("create member payload", email=MEMBER_EMAIL, name=MEMBER_NAME)
            create_resp = member_svc.create_member_success(
                MEMBER_EMAIL,
                name=MEMBER_NAME,
                client=admin_client,
            )
            member_id = create_resp.get("id") or (create_resp.get("member") or {}).get("id")
            assert member_id, f"创建成员响应中缺少 id: {create_resp}"
            resource_tracker.add_member(member_id)
            log_resource_ids(member_id=member_id)
            log_step_result("create member result", create_resp)
            #审计日志同步需要时间，这里暂定10s等待，后续可根据通过率和性能调整
            time.sleep(10)
        # Step 2: 查询审计日志（创建成员的记录）
        with allure.step("Step2: 查看审计日志记录（创建成员）"):
            start_time, end_time = _today_start_end_utc()
            log_step_data("audit query params", start_time=start_time, end_time=end_time, resource_id=member_id)
            audit_svc = AuditService()
            data = audit_svc.list_events_success(
                client=admin_client,
                start_time=start_time,
                end_time=end_time,
                resource_type=RESOURCE_TYPE_MEMBER,
                resource_id=member_id,
                operation_type=OPERATION_TYPE_CREATE,
                page_size=10,
                cursor_direction=CURSOR_DIRECTION_NEXT,
            )
            events = data.get("events") or []
            # 断言存在创建成员的审计记录（可进一步按 member_id / email / resourceName 校验）
            create_events = [
                e
                for e in events
                if isinstance(e, dict)
                and e.get("operation") == OPERATION_TYPE_CREATE
                and e.get("resourceType") == RESOURCE_TYPE_MEMBER
            ]
            assert len(create_events) >= 1, (
                f"审计日志中未查到创建成员记录，resourceType={RESOURCE_TYPE_MEMBER}, "
                f"operationType={OPERATION_TYPE_CREATE}, events={events}"
            )
            log_step_result("audit query result", {"events_count": len(events), "matched_events": create_events})
