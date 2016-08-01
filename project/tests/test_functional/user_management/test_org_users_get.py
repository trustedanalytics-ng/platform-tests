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
from modules.tap_object_model import Organization, User
from tests.fixtures.test_data import TestData


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class GetOrganizationUsers(TapTestCase):

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def users(cls, request, test_org, class_context):
        cls.step("Create test users")
        manager = User.api_create_by_adding_to_organization(class_context, org_guid=test_org.guid)
        cls.manager_client = manager.login()
        auditor = User.api_create_by_adding_to_organization(class_context, org_guid=test_org.guid,
                                                            roles=User.ORG_ROLES["auditor"])
        cls.auditor_client = auditor.login()
        billing_manager = User.api_create_by_adding_to_organization(class_context, org_guid=test_org.guid,
                                                                    roles=User.ORG_ROLES["billing_manager"])
        cls.billing_manager_client = billing_manager.login()

    @pytest.fixture(scope="function")
    def setup_context(self, context):
        # TODO no longer needed when this class removes unittest dependency
        self.context = context

    def _cannot_get_org_users(self, client):
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            User.api_get_list_via_organization, org_guid=TestData.test_org.guid,
                                            client=client)

    @priority.low
    def test_org_auditor_cannot_get_org_users(self):
        self.step("Check that auditor cannot get list of users in org")
        self._cannot_get_org_users(client=self.auditor_client)

    @priority.low
    def test_billing_manager_cannot_get_org_users(self):
        self.step("Check that billing manager cannot get list of users in org")
        self._cannot_get_org_users(client=self.billing_manager_client)

    @priority.high
    def test_manager_can_get_org_users(self):
        self.step("Check that manager can get list of users in org")
        expected_users = User.api_get_list_via_organization(org_guid=TestData.test_org.guid)
        user_list = User.api_get_list_via_organization(org_guid=TestData.test_org.guid, client=self.manager_client)
        self.assertUnorderedListEqual(user_list, expected_users)

    @priority.low
    @pytest.mark.usefixtures("setup_context")
    def test_user_not_in_org_cannot_get_org_users(self):
        self.step("Create new org")
        org = Organization.api_create(self.context)
        self.step("Check that the user cannot get list of users in the test org")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            User.api_get_list_via_organization, org_guid=org.guid,
                                            client=self.manager_client)
