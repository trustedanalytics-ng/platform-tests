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

import pytest

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.markers import components, priority
from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import Organization, User


logged_components = (TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)


class BaseTestClass(TapTestCase):
    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def users(cls, request, test_org):
        cls.test_org = test_org
        cls.step("Create users for org tests")
        cls.test_user = User.api_create_by_adding_to_organization(org_guid=cls.test_org.guid)
        cls.test_client = cls.test_user.login()
        cls.second_test_user = User.api_create_by_adding_to_organization(org_guid=cls.test_org.guid)

        def fin():
            cls.test_user.cf_api_delete()
            cls.second_test_user.cf_api_delete()
        request.addfinalizer(fin)


class AddNewUserToOrganization(BaseTestClass):
    pytestmark = [components.user_management, components.auth_gateway, components.auth_proxy]

    def _get_test_org(self):
        return self.test_org

    def _add_test_user(self, org_guid, roles, client=None):
        self.step("Create new user by adding to an organization with roles {}.".format(roles))
        return User.api_create_by_adding_to_organization(org_guid=org_guid, roles=roles, inviting_client=client)

    def _get_inviting_client(self, org_guid=None):
        return self.test_client

    @priority.medium
    def test_add_user_with_no_roles(self):
        org = self._get_test_org()
        expected_roles = []
        user = self._add_test_user(org.guid, expected_roles)
        self.assert_user_in_org_and_roles(user, org.guid, expected_roles)

    @priority.high
    def test_admin_adds_user_one_role(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                org = self._get_test_org()
                user = self._add_test_user(org_guid=org.guid, roles=expected_roles)
                self.assert_user_in_org_and_roles(user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_user_all_roles(self):
        org = self._get_test_org()
        expected_roles = self.ALL_ROLES
        user = self._add_test_user(org_guid=org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(user, org.guid, expected_roles)

    @priority.medium
    def test_org_manager_adds_user(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                org = self._get_test_org()
                inviting_client = self._get_inviting_client(org.guid)
                self.step("Org manager adds a new user to an organization with roles {}".format(expected_roles))
                new_user = self._add_test_user(org_guid=org.guid, roles=expected_roles, client=inviting_client)
                self.assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @priority.medium
    def test_non_manager_cannot_add_user_to_org(self):
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_client = self.test_client
                self.step("Create new organization and add test user as {}".format(non_manager_roles))
                org = Organization.api_create()
                self.step("Check that user cannot be added to organization by non-manager")
                org_users = User.api_get_list_via_organization(org.guid)
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    self._add_test_user, org_guid=org.guid,
                                                    roles=User.ORG_ROLES["auditor"], client=inviting_client)
                # assert user list did not change
                self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @priority.low
    def test_cannot_add_user_to_non_existing_org(self):
        invalid_org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that an error is raised when trying to add user using incorrect org guid")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            self._add_test_user, org_guid=invalid_org_guid, roles=roles)

    @priority.low
    def test_cannot_add_new_user_incorrect_role(self):
        roles = ["i-don't-exist"]
        org = self._get_test_org()
        org_users = User.api_get_list_via_organization(org.guid)
        self.step("Check that error is raised when trying to add user using incorrect roles")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMPTY, self._add_test_user,
                                            org_guid=org.guid, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)


class AddExistingUserToOrganization(AddNewUserToOrganization):
    pytestmark = [components.user_management]

    def _get_test_org(self):
        self.step("Create organization")
        return Organization.api_create()

    def _add_test_user(self, org_guid, roles, client=None):
        self.step("Add a platform user to organization with roles {}.".format(roles))
        self.second_test_user.api_add_to_organization(org_guid=org_guid, roles=roles, client=client)
        return self.second_test_user

    def _get_inviting_client(self, org_guid=None):
        self.test_user.api_add_to_organization(org_guid, roles=User.ORG_ROLES["manager"])
        return self.test_client


class AddUserToOrganization(BaseTestClass):
    pytestmark = [components.user_management]

    @priority.low
    def test_cannot_add_new_user_with_non_email_username(self):
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

    @priority.medium
    def test_user_cannot_add_themselves_to_org(self):
        invited_user, inviting_client = self.test_user, self.test_client
        expected_roles = User.ORG_ROLES["auditor"]
        self.step("Create an organization.")
        org = Organization.api_create()
        org_users = User.api_get_list_via_organization(org.guid)
        self.step("Check that a platform user is not able to add themselves to the organization")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            invited_user.api_add_to_organization, org_guid=org.guid,
                                            roles=expected_roles, client=inviting_client)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

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
