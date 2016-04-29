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

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, priority
from modules.tap_object_model import Organization, User
from tests.fixtures import setup_fixtures, teardown_fixtures


@log_components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
@components(TAP.user_management)
class AddExistingUserToOrganization(TapTestCase):
    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Create users for org tests")
        users, _ = setup_fixtures.create_test_users(2)
        cls.test_user = users[0]
        cls.test_client = users[0].login()
        cls.second_test_user = users[1]

    def _assert_user_not_in_org(self, user, org_guid):
        self.step("Check that the user is not in the organization.")
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertNotIn(user, org_users, "User is among org users, although they shouldn't")

    @priority.medium
    def test_add_existing_user_with_no_roles(self):
        invited_user = self.test_user
        expected_roles = []
        self.step("Create an organization.")
        org = Organization.api_create()
        self.step("Add a platform user to organization with no roles.")
        invited_user.api_add_to_organization(org_guid=org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.high
    def test_admin_adds_existing_user_one_role(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                invited_user = self.test_user
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user to organization with roles {}.".format(expected_roles))
                invited_user.api_add_to_organization(org.guid, roles=expected_roles)
                self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_existing_user_all_roles(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = self.ALL_ROLES
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_user_which_is_already_in_org_with_the_same_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["manager"]
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self.step("Add the same user to the same organization with the same roles")
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_user_which_is_already_in_org_with_different_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        roles_0 = User.ORG_ROLES["manager"]
        roles_1 = User.ORG_ROLES["auditor"]
        expected_roles = roles_0 | roles_1  # adding user with a new role results in the user having sum of the roles
        self.step("Add a platform user to organization with roles {}.".format(roles_0))
        invited_user.api_add_to_organization(org.guid, roles=roles_0)
        self.step("Add the same user to the same organization with roles {}".format(roles_1))
        invited_user.api_add_to_organization(org.guid, roles=roles_1)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.medium
    def test_org_manager_adds_existing_user(self):
        invited_user = self.second_test_user
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user as manager to the organization.")
                inviting_user.api_add_to_organization(org.guid, roles=User.ORG_ROLES["manager"])
                self.step("The new manager adds a platform user to the organization.")
                invited_user.api_add_to_organization(org.guid, roles=expected_roles, client=inviting_client)
                self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.medium
    def test_non_manager_cannot_add_existing_user_to_org(self):
        invited_user = self.second_test_user
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user as non-manager to the organization.")
                inviting_user.api_add_to_organization(org.guid, roles=non_manager_roles)
                expected_roles = User.ORG_ROLES["auditor"]
                self.step("Check that the non-manager is able to add a platform user to the org")
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    invited_user.api_add_to_organization, org_guid=org.guid,
                                                    roles=expected_roles, client=inviting_client)
                self._assert_user_not_in_org(invited_user, org.guid)

    @priority.medium
    def test_user_cannot_add_themselves_to_org(self):
        invited_user, inviting_client = self.test_user, self.test_client
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["auditor"]
        self.step("Check that a platform user is not able to add themselves to the organization")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            invited_user.api_add_to_organization, org_guid=org.guid,
                                            roles=expected_roles, client=inviting_client)
        self._assert_user_not_in_org(invited_user, org.guid)

    @priority.low
    def test_cannot_add_existing_user_to_non_existing_org(self):
        invited_user = self.test_user
        invalid_org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that adding user to organization using invalid org guid raises an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            invited_user.api_add_to_organization, org_guid=invalid_org_guid,
                                            roles=roles)

    @priority.low
    def test_cannot_add_existing_user_with_incorrect_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        invalid_role = ["incorrect-role"]
        self.step("Check that it is not possible to add user to the organization with role {}".format(invalid_role))
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            invited_user.api_add_to_organization, org_guid=org.guid, roles=invalid_role)
        self._assert_user_not_in_org(invited_user, org.guid)
