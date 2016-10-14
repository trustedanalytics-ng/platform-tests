#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, User
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestGetOrganizationUsers:

    @pytest.fixture(scope="class")
    def test_org_user_clients(self, test_org_admin_client, test_org_user_client):
        return {
            "test_org_admin_client": test_org_admin_client,
            "test_org_user_client": test_org_user_client
        }
    
    @priority.high
    @pytest.mark.skip(reason="DPNG-10987 User-management is not able to add admin user (blocked prerequisite)")
    def test_org_admin_can_get_org_users(self, test_org, test_org_admin_client):
        step("Check that admin can get a list of users in org")
        expected_users = User.get_list_in_organization(org_guid=test_org.guid, client=test_org_admin_client)
        user_list = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(user_list) == sorted(expected_users)

    @priority.high
    @pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
    def test_platform_admin_can_get_org_users(self, admin_user, test_org, admin_client, remove_admin_from_test_org):
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        step("Check that platform admin can get a list of users in any org")
        expected_users = User.get_list_in_organization(org_guid=test_org.guid, client=admin_client)
        user_list = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(user_list) == sorted(expected_users)

    @priority.low
    def test_org_user_cannot_get_org_users(self, test_org_user_client, test_org):
        step("Check that user cannot get list of users in org")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     User.get_list_in_organization, org_guid=test_org.guid,
                                     client=test_org_user_client)
