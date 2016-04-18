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

import time

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, priority
from modules.tap_object_model import Organization, User
from tests.fixtures import setup_fixtures, teardown_fixtures


@log_components()
@components(TAP.user_management, TAP.auth_gateway)
class AddNewUserToOrganization(TapTestCase):
    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Create users for org tests")
        users, cls.test_org = setup_fixtures.create_test_users(2)
        cls.test_user = users[0]
        cls.test_client = users[0].login()
        cls.second_test_user = users[1]

    @priority.medium
    def test_add_new_user_with_no_roles(self):
        org = self.test_org
        expected_roles = []
        self.step("Create new user by adding to an organization with no roles")
        invited_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.high
    def test_admin_adds_new_user_one_role(self):
        org = self.test_org
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                self.step("Create new user by adding to an organization with roles {}".format(expected_roles))
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
                self.assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_new_user_all_roles(self):
        org = self.test_org
        expected_roles = self.ALL_ROLES
        self.step("Create new user by adding to an organization with roles {}".format(expected_roles))
        new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @priority.medium
    def test_org_manager_adds_new_user(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_client = self.test_client
                org = self.test_org
                self.step("Org manager adds a new user to an organization with roles {}".format(expected_roles))
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles,
                                                                     inviting_client=inviting_client)
                self.assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @priority.medium
    def test_non_manager_cannot_add_new_user_to_org(self):
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create new organization and add test user as {}".format(non_manager_roles))
                org = Organization.api_create()
                inviting_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                self.step("Check that user cannot be added to organization by non-manager")
                org_users = User.api_get_list_via_organization(org.guid)
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    User.api_create_by_adding_to_organization, org_guid=org.guid,
                                                    roles=User.ORG_ROLES["auditor"], inviting_client=inviting_client)
                # assert user list did not change
                self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @priority.low
    def test_cannot_add_user_with_non_email_username(self):
        org = self.test_org
        self.step("Check that user with non valid username cannot be added to an organization")
        org_users = User.api_get_list_via_organization(org.guid)
        username = "non-valid-username{}".format(time.time())
        roles = self.ALL_ROLES
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_organization, org_guid=org.guid,
                                            username=username, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @priority.low
    def test_cannot_add_new_user_to_non_existing_org(self):
        org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that an error is raised when trying to add user using incorrect org guid")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            User.api_create_by_adding_to_organization, org_guid=org_guid, roles=roles)

    @priority.low
    def test_cannot_add_new_user_incorrect_role(self):
        org = self.test_org
        org_users = User.api_get_list_via_organization(org.guid)
        roles = ["i-don't-exist"]
        self.step("Check that error is raised when trying to add user using incorrect roles")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMPTY,
                                            User.api_create_by_adding_to_organization, org_guid=org.guid, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)
