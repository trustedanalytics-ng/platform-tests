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

import itertools

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.http_calls import platform as api
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, priority
from modules.tap_object_model import Organization, User
from tests.fixtures import setup_fixtures, teardown_fixtures


@log_components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
@components(TAP.user_management)
class UpdateOrganizationUser(TapTestCase):
    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]
    ROLES_WITHOUT_MANAGER = [(name, user_role) for name, user_role in User.ORG_ROLES.items() if name is not "manager"]

    client_permission = {
        "admin": True,
        "manager": True,
        "auditor": False,
        "billing_manager": False
    }

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Create users for org tests")
        users, cls.test_org = setup_fixtures.create_test_users(2)
        cls.test_user = users[0]
        cls.test_client = users[0].login()
        cls.second_test_user = users[1]

    def _get_client(self, client_name):
        if client_name == "admin":
            return None
        return self.test_client

    def _add_test_user_to_org(self, user, org, roles):
        self.step("Add user with {} role(s)".format(roles))
        user.api_add_to_organization(org.guid, roles=roles)
        return user

    def _create_org_and_init_users(self, tested_client_type, test_user_initial_roles=None):
        """
        Method creates organization and adds two users to it (if all parameters are provided).
        :param tested_client_type: Type of user and client to create (admin, manager, billing_manager, auditor)
        :param test_user_initial_roles: Initial roles for the user on which we want perform update tests
        :return: org - created organization, testing_user - the user which will be used to update other users ,
        user_client - client of testing_user, test_user - the user which will be updated in tests
        """
        self.step("Create test org")
        org = Organization.api_create()
        testing_user = test_user = None
        user_client = self._get_client(tested_client_type)
        if user_client:
            testing_user = self._add_test_user_to_org(self.test_user, org, User.ORG_ROLES[tested_client_type])
        if test_user_initial_roles is not None:
            test_user = self._add_test_user_to_org(self.second_test_user, org, test_user_initial_roles)
        return org, testing_user, user_client, test_user

    def _update_roles_with_client(self, client_name, init_roles, updated_roles, is_authorized, msg):
        org, _, client, updated_user = self._create_org_and_init_users(client_name, init_roles)
        self.step(msg)
        with self.subTest(user_type=client_name, new_role=updated_roles):
            if is_authorized:
                updated_user.api_update_org_roles(org.guid, new_roles=updated_roles, client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, updated_roles)
            else:
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid,
                                                    new_roles=updated_roles, client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, init_roles)

    @priority.high
    def test_update_org_user_add_new_role(self):
        permissions, roles = self.client_permission.items(), User.ORG_ROLES.values()
        for (client_name, is_authorized), new_role in itertools.product(permissions, roles):
            self._update_roles_with_client(client_name, {}, new_role, is_authorized,
                                           "As {} try to add new role {} to user".format(client_name, new_role))

    @priority.medium
    def test_update_org_user_remove_role(self):
        permissions, roles = self.client_permission.items(), self.NON_MANAGER_ROLES
        for (client_name, is_authorized), role in itertools.product(permissions, roles):
            self._update_roles_with_client(client_name, self.ALL_ROLES, self.ALL_ROLES - {role}, is_authorized,
                                           "As {} try to remove user role {}".format(client_name, {role}))

    @priority.medium
    def test_update_org_user_change_role(self):
        initial_roles = User.ORG_ROLES["auditor"]
        expected_roles = User.ORG_ROLES["billing_manager"]
        for client_name, is_authorized in self.client_permission.items():
            self._update_roles_with_client(client_name, initial_roles, expected_roles, is_authorized,
                                           "As {} try to change user roles".format(client_name))

    @priority.low
    def test_update_org_user_with_the_same_role(self):
        permissions, roles = self.client_permission.items(), User.ORG_ROLES.values()
        for (client_name, is_authorized), role in itertools.product(permissions, roles):
            self._update_roles_with_client(client_name, role, role, is_authorized,
                                           "As {} update user with same role".format(client_name))

    @priority.low
    def test_cannot_remove_manager_role_for_the_only_org_manager(self):
        expected_roles = self.ALL_ROLES
        org, _, client, updated_user = self._create_org_and_init_users("admin", expected_roles)
        self.step("Check that removing manager role of the only org manager as admin, returns an error")
        new_roles = expected_roles - User.SPACE_ROLES["manager"]
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            updated_user.api_update_org_roles, org_guid=org.guid,
                                            new_roles=new_roles, client=client)
        self.assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    @priority.low
    def test_user_cannot_update_user_in_org_where_they_are_not_added(self):
        initial_role = User.ORG_ROLES["billing_manager"]
        role = User.ORG_ROLES["auditor"]
        self.step("Create test organization")
        org = Organization.api_create()
        self.step("Add test user to org")
        updated_user = self.second_test_user
        updated_user.api_add_to_organization(org.guid, roles=initial_role)
        self.step("Test that users cannot change roles of users from another org")
        for user_role in User.ORG_ROLES.values():
            other_org = Organization.api_create()
            self.test_user.api_add_to_organization(other_org.guid, roles=user_role)
            with self.subTest(user_type=user_role):
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid, new_roles=role,
                                                    client=self.test_client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, initial_role)

    @priority.low
    def test_cannot_update_user_which_is_not_in_org(self):
        user_not_in_org = self.second_test_user
        self.step("Create test organization")
        org = Organization.api_create()
        self.step("Check that attempt to update a user via org they are not in returns an error")
        org_users = User.api_get_list_via_organization(org.guid)
        self.step("Get only clients that are authorized to update other users roles")
        tested_clients = [client_name for client_name, is_authorized in self.client_permission.items() if is_authorized]
        for client_name in tested_clients:
            with self.subTest(client_type=client_name):
                client = self._get_client(client_name)
                if client_name == "admin":
                    self.assertRaisesUnexpectedResponse(
                        HttpStatus.CODE_NOT_FOUND,
                        HttpStatus.MSG_USER_NOT_EXIST_IN_ORGANIZATION.format(user_not_in_org.guid, org.guid),
                        user_not_in_org.api_update_org_roles, org_guid=org.guid, new_roles=User.ORG_ROLES["auditor"],
                        client=client)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        user_not_in_org.api_update_org_roles, org_guid=org.guid,
                                                        new_roles=User.ORG_ROLES["auditor"], client=client)
                self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @priority.low
    def test_change_org_manager_role_in_org_with_two_managers(self):
        manager_roles = User.ORG_ROLES["manager"]
        new_roles = self.NON_MANAGER_ROLES
        org, _, _, updated_user = self._create_org_and_init_users("manager", manager_roles)
        self.step("Check that it's possible to remove manager role from the user")
        updated_user.api_update_org_roles(org_guid=org.guid, new_roles=new_roles)
        self.assert_user_in_org_and_roles(updated_user, org.guid, new_roles)

    @priority.low
    def test_cannot_update_non_existing_org_user(self):
        org = self.test_org
        invalid_guid = "invalid-user-guid"
        roles = User.ORG_ROLES["billing_manager"]
        self.step("Check that updating user which is not in an organization returns an error")
        org_users = User.api_get_list_via_organization(org_guid=org.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            api.api_update_org_user_roles, org_guid=org.guid, user_guid=invalid_guid,
                                            new_roles=roles)
        self.assertListEqual(User.api_get_list_via_organization(org_guid=org.guid), org_users)

    @priority.low
    def test_cannot_update_org_user_in_non_existing_org(self):
        invalid_guid = "invalid-org-guid"
        user_guid = self.second_test_user.guid
        roles = User.ORG_ROLES["billing_manager"]
        self.step("Check that updating user using invalid org guid returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            api.api_update_org_user_roles, org_guid=invalid_guid, user_guid=user_guid,
                                            new_roles=roles)

    @priority.low
    def test_cannot_update_org_user_with_incorrect_role(self):
        initial_roles = User.ORG_ROLES["billing_manager"]
        invalid_roles = ["invalid role"]
        for client_name, _ in self.ROLES_WITHOUT_MANAGER:
            org, _, _, updated_user = self._create_org_and_init_users(client_name, initial_roles)
            self.step("Check that updating user using invalid role returns an error")
            self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                                updated_user.api_update_org_roles, org_guid=org.guid,
                                                new_roles=invalid_roles)
            self.assert_user_in_org_and_roles(updated_user, org.guid, initial_roles)

    @priority.low
    def test_update_role_of_one_org_manager_cannot_update_second(self):
        manager_role = User.ORG_ROLES["manager"]
        org, first_user, _, second_user = self._create_org_and_init_users("manager", manager_role)
        self.step("Remove manager role from one of the managers")
        first_user.api_update_org_roles(org_guid=org.guid, new_roles=self.NON_MANAGER_ROLES)
        self.step("Check that attempt to remove manager role from the second manager returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            second_user.api_update_org_roles, org_guid=org.guid,
                                            new_roles=self.NON_MANAGER_ROLES)
        self.assert_user_in_org_and_roles(first_user, org.guid, self.NON_MANAGER_ROLES)
        self.assert_user_in_org_and_roles(second_user, org.guid, manager_role)

    @priority.low
    def test_non_manager_users_cannot_change_their_roles(self):
        self.step("Test non org managers cannot change their roles")
        for client_name, user_role in self.ROLES_WITHOUT_MANAGER:
            org, updated_user, client, _ = self._create_org_and_init_users(client_name)
            new_roles = self.NON_MANAGER_ROLES - user_role
            self.step("Try to change role as '{}'".format(client_name))
            with self.subTest(user_type=user_role):
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid, new_roles=new_roles,
                                                    client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, user_role)

    @priority.low
    def test_non_manager_users_cannot_change_their_roles_to_org_manager(self):
        for client_name, user_role in self.ROLES_WITHOUT_MANAGER:
            org, updated_user, client, _ = self._create_org_and_init_users(client_name)
            self.step("Try to change role as '{}'".format(client_name))
            with self.subTest(user_type=user_role):
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid,
                                                    new_roles=User.ORG_ROLES["manager"], client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, user_role)

    @priority.low
    def test_org_manager_cannot_delete_own_role_while_being_the_only_org_manager(self):
        manager_role = User.ORG_ROLES["manager"]
        org, updated_user, client, _ = self._create_org_and_init_users("manager")
        self.step("As org manager try to delete self 'org manager' role")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            updated_user.api_update_org_roles, org.guid, new_roles={}, client=client)
        self.assert_user_in_org_and_roles(updated_user, org.guid, manager_role)

    @priority.low
    def test_org_manager_removes_own_role_when_there_is_another_org_manager(self):
        manager_role = User.ORG_ROLES["manager"]
        org, updated_user, client, _ = self._create_org_and_init_users("manager", manager_role)
        self.step("As one of the org managers delete own 'org manager' role")
        updated_user.api_update_org_roles(org.guid, new_roles={}, client=client)
        self.assert_user_in_org_and_roles(updated_user, org.guid, {})

    @priority.medium
    def test_org_manager_add_roles_to_self(self):
        expected_role = User.ORG_ROLES["manager"]
        org, updated_user, client, _ = self._create_org_and_init_users("manager")
        self.step("As org manager add to yourself new roles")
        for _, user_role in self.ROLES_WITHOUT_MANAGER:
            expected_role = expected_role | user_role
            updated_user.api_update_org_roles(org.guid, new_roles=expected_role, client=client)
            self.assert_user_in_org_and_roles(updated_user, org.guid, expected_role)

    @priority.low
    def test_send_org_role_update_request_with_empty_body(self):
        expected_roles = User.ORG_ROLES["manager"]
        self.step("Create new platform user by adding to org")
        test_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid, roles=expected_roles)
        self.step("Send request with empty body")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_CANNOT_PERFORM_REQ_WITHOUT_ROLES,
                                            api.api_update_org_user_roles, self.test_org.guid, test_user.guid)
        self.assert_user_in_org_and_roles(test_user, self.test_org.guid, expected_roles)
