import unittest

import allure

from fixtures.auth_fixture import admin_client
from services.member_service import MemberService
from utils.test_log import log_step_data


@allure.epic("Dify Enterprise")
@allure.feature("Member Management")
class TestMembersTestCase:

    @allure.story("CURD Member Placeholder")
    @allure.severity(allure.severity_level.MINOR)
    def test_curd_member(self):
        pass

    @allure.story("Delete Member By ID")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_member_success(self, admin_client):
        member_svc = MemberService()
        log_step_data("delete member payload", member_id="388be05c-dc73-4358-8016-7ca669d77f52")
        member_svc.delete_member_success(member_id="ea1e9d92-2b10-494c-aeab-76ddab187ad4")
