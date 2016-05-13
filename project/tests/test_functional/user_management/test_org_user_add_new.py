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
from modules.markers import components, priority
from modules.tap_object_model import Organization, User


logged_components = (TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
pytestmark = [components.user_management, components.auth_gateway, components.auth_proxy]


class AddNewUserToOrganization(TapTestCase):

    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def setup(cls, request, test_org_manager, test_org_manager_client, class_context):
        cls.step("Create test org")
        cls.test_org = Organization.api_create(class_context)
        cls.step("Add org manager")
        cls.org_manager = test_org_manager
        cls.org_manager_client = test_org_manager_client
        cls.org_manager.api_add_to_organization(org_guid=cls.test_org.guid)

    @pytest.fixture(scope="function", autouse=True)
    def setup_context(self, context):
        # TODO move to methods when dependency on unittest is removed
        self.context = context

    @priority.medium
    def test_add_new_user_with_no_roles(self):
        self.step("Create new user by adding to an organization with no roles")
        expected_roles = []
        self.user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                              roles=expected_roles)
        self.assert_user_in_org_and_roles(self.user, self.test_org.guid, expected_roles)

    @priority.high
    def test_admin_adds_new_user_one_role(self):
        # TODO parametrize
        self.step("Create new user by adding to an organization with one role")
        expected_roles = User.ORG_ROLES["auditor"]
        self.user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                              roles=expected_roles)
        self.assert_user_in_org_and_roles(self.user, self.test_org.guid, expected_roles)

    @priority.low
    def test_admin_adds_new_user_all_roles(self):
        self.step("Create new user by adding to an organization with all roles")
        expected_roles = self.ALL_ROLES
        self.user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                              roles=expected_roles)
        self.assert_user_in_org_and_roles(self.user, self.test_org.guid, expected_roles)

    @priority.medium
    def test_org_manager_adds_new_user(self):
        self.step("Org manager adds a new user to an organization with")
        inviting_client = self.org_manager_client
        expected_roles = User.ORG_ROLES["billing_manager"]
        self.user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                              roles=expected_roles, inviting_client=inviting_client)
        self.assert_user_in_org_and_roles(self.user, self.test_org.guid, expected_roles)

    @priority.medium
    def test_non_manager_cannot_add_new_user_to_org(self):
        self.step("Add a non-manager to the organization.")
        non_manager = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                                roles=User.ORG_ROLES["auditor"])
        self.user = non_manager
        non_manager_client = non_manager.login()
        self.step("Check that user cannot be added to organization by non-manager")
        org_users = User.api_get_list_via_organization(self.test_org.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            User.api_create_by_adding_to_organization, self.context,
                                            org_guid=self.test_org.guid, roles=User.ORG_ROLES["auditor"],
                                            inviting_client=non_manager_client)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(self.test_org.guid), org_users)

    @priority.low
    # not in existing users
    def test_cannot_add_user_with_non_email_username(self):
        self.step("Check that user with non valid username cannot be added to an organization")
        username = "non-valid-username"
        roles = self.ALL_ROLES
        org_users = User.api_get_list_via_organization(self.test_org.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_organization, self.context,
                                            org_guid=self.test_org.guid, username=username, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(self.test_org.guid), org_users)

    @priority.low
    def test_cannot_add_new_user_to_non_existing_org(self):
        org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that an error is raised when trying to add user using incorrect org guid")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            User.api_create_by_adding_to_organization, self.context, org_guid=org_guid,
                                            roles=roles)

    @priority.low
    def test_cannot_add_new_user_incorrect_role(self):
        self.step("Check that error is raised when trying to add user using incorrect roles")
        roles = ["i-don't-exist"]
        org_users = User.api_get_list_via_organization(self.test_org.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMPTY,
                                            User.api_create_by_adding_to_organization, self.context,
                                            org_guid=self.test_org.guid, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(self.test_org.guid), org_users)
