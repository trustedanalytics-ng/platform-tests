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


@log_components()
@components(TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
class DeleteOrganizationUser(TapTestCase):
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

    def _assert_user_not_in_org(self, user, org_guid):
        self.step("Check that the user is not in the organization.")
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertNotIn(user, org_users, "User is among org users, although they shouldn't")

    @priority.medium
    def test_admin_deletes_the_only_org_user_non_manager(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        for non_manager_role in self.NON_MANAGER_ROLES:
            non_manager_role = [non_manager_role]
            with self.subTest(roles=non_manager_role):
                self.step("Add user to organization with role {}".format(non_manager_role))
                deleted_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_role)
                self.step("Remove the user from the organization")
                deleted_user.api_delete_from_organization(org.guid)
                self._assert_user_not_in_org(deleted_user, org.guid)

    @priority.low
    def test_admin_cannot_delete_the_only_org_manager(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        roles = User.ORG_ROLES["manager"]
        self.step("Add user to organization as manager")
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        self.step("Check that the only manager cannot be removed from the organization")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            deleted_user.api_delete_from_organization, org_guid=org.guid)
        self.assert_user_in_org_and_roles(deleted_user, org.guid, roles)

    @priority.high
    def test_admin_deletes_one_of_org_users(self):
        not_deleted_user = self.test_user
        not_deleted_user_roles = User.ORG_ROLES["auditor"]
        deleted_user_roles = User.ORG_ROLES["billing_manager"]
        deleted_user = self.second_test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add two non-manager users to the organization")
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=deleted_user_roles)
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=not_deleted_user_roles)
        self.step("Remove one of the users from the organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self.assert_user_in_org_and_roles(not_deleted_user, org.guid, not_deleted_user_roles)
        self._assert_user_not_in_org(deleted_user, org.guid)

    @priority.low
    def test_admin_deletes_one_of_org_managers_cannot_delete_second(self):
        roles = User.ORG_ROLES["manager"]
        not_deleted_user = self.test_user
        deleted_user = self.second_test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add two managers to the organization")
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        self.step("Remove one of the managers from the organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self._assert_user_not_in_org(deleted_user, org.guid)
        self.step("Check that removing the last org manager returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            not_deleted_user.api_delete_from_organization, org_guid=org.guid)
        self.assert_user_in_org_and_roles(not_deleted_user, org.guid, roles)

    @priority.low
    def test_admin_updates_role_of_one_org_manager_cannot_delete_second(self):
        manager_role = User.ORG_ROLES["manager"]
        for updated_user_roles in self.NON_MANAGER_ROLES:
            updated_user_roles = [updated_user_roles]
            with self.subTest(updated_rols=updated_user_roles):
                manager_user = self.test_user
                updated_user = self.second_test_user
                self.step("Create a test organization")
                org = Organization.api_create()
                self.step("Add two managers to the organization")
                manager_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
                updated_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
                self.step("Update roles of one of the managers to {}".format(updated_user_roles))
                updated_user.api_update_org_roles(org_guid=org.guid, new_roles=updated_user_roles)
                self.assert_user_in_org_and_roles(updated_user, org.guid, updated_user_roles)
                self.step("Check that removing the last manger returns an error")
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                                    manager_user.api_delete_from_organization, org_guid=org.guid)
                self.assert_user_in_org_and_roles(manager_user, org.guid, manager_role)

    @priority.low
    def test_admin_cannot_delete_org_user_twice(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add test user to organization")
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=User.ORG_ROLES["auditor"])
        self.step("Delete test user from organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self.step("Try to delete test user from organization second time")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY,
                                            deleted_user.api_delete_from_organization, org_guid=org.guid)

    @priority.low
    def test_admin_cannot_delete_non_existing_org_user(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Check that an attempt to delete user which is not in org returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY,
                                            deleted_user.api_delete_from_organization, org_guid=org.guid)

    @priority.high
    def test_org_manager_can_delete_another_user(self):
        self.step("Create a test organization")
        org = Organization.api_create()
        manager_role = User.ORG_ROLES["manager"]
        self.step("Add org manager to organization")
        self.test_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
        user_client = self.test_client
        deleted_user = self.second_test_user
        for roles in User.ORG_ROLES.values():
            with self.subTest(deleted_user_roles=roles):
                self.step("Add user to the test org with roles {}".format(roles))
                deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
                self.step("Org manager removes the user from the test org")
                deleted_user.api_delete_from_organization(org_guid=org.guid, client=user_client)
                self._assert_user_not_in_org(deleted_user, org.guid)

    @priority.low
    def test_non_manager_cannot_delete_user(self):
        deleted_user_roles = User.ORG_ROLES["auditor"]
        non_manager_user, non_manager_client = self.test_user, self.test_client
        deleted_user = self.second_test_user
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(non_manager_roles=non_manager_roles):
                self.step("Create a test organization")
                org = Organization.api_create()
                self.step("Add deleting user to the organization with roles {}".format(non_manager_roles))
                non_manager_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                self.step("Add deleted user to the organization with roles {}".format(deleted_user_roles))
                deleted_user.api_add_to_organization(org_guid=org.guid, roles=deleted_user_roles)
                self.step("Check that non-manager cannot delete user from org")
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    deleted_user.api_delete_from_organization, org_guid=org.guid,
                                                    client=non_manager_client)
                self.assert_user_in_org_and_roles(deleted_user, org.guid, deleted_user_roles)