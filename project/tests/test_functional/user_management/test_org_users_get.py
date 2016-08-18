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
from modules.runner.tap_test_case import TapTestCase
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, User
from tests.fixtures.assertions import assert_raises_http_exception
from tests.fixtures.test_data import TestData


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestGetOrganizationUsers:

    @staticmethod
    def _cannot_get_org_users(client, test_org_guid):
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     User.api_get_list_via_organization, org_guid=test_org_guid,
                                     client=client)

    @priority.low
    def test_org_auditor_cannot_get_org_users(self, test_org, test_org_auditor_client):
        step("Check that auditor cannot get list of users in org")
        self._cannot_get_org_users(client=test_org_auditor_client, test_org_guid=test_org.guid)

    @priority.low
    def test_billing_manager_cannot_get_org_users(self, test_org, test_org_billing_manager_client):
        step("Check that billing manager cannot get list of users in org")
        self._cannot_get_org_users(client=test_org_billing_manager_client, test_org_guid=test_org.guid)

    @priority.high
    def test_manager_can_get_org_users(self, test_org, test_org_manager_client):
        step("Check that manager can get list of users in org")
        expected_users = User.api_get_list_via_organization(org_guid=TestData.test_org.guid)
        user_list = User.api_get_list_via_organization(org_guid=test_org.guid, client=test_org_manager_client)
        assert sorted(user_list) == sorted(expected_users)

    @priority.low
    def test_user_not_in_org_cannot_get_org_users(self, context, test_org_manager_client):
        step("Create new org")
        org = Organization.api_create(context)
        step("Check that the user cannot get list of users in the test org")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     User.api_get_list_via_organization, org_guid=org.guid,
                                     client=test_org_manager_client)
