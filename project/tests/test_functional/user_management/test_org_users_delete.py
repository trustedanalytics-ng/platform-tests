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
from tests.fixtures import test_data


logged_components = (TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
pytestmark = [components.user_management, components.auth_gateway, components.auth_proxy]


class DeleteOrganizationUser(TapTestCase):

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def setup(cls, request, class_context):
        cls.step("Create test org")
        cls.test_org = Organization.api_create(class_context)

    @pytest.fixture(scope="function", autouse=True)
    def setup_context(self, context):
        # TODO move to methods when dependency on unittest is removed
        self.context = context

    def _assert_user_not_in_org(self, user, org_guid):
        # TODO refactor to fixtures.assertions
        self.step("Check that the user is not in the organization.")
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertNotIn(user, org_users, "User is among org users, although they shouldn't")

    @priority.medium
    def test_admin_deletes_non_manager(self):
        self.step("Add a non-manager user to organization.")
        user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                         roles=User.ORG_ROLES["auditor"])
        self.step("Remove the user from the organization")
        user.api_delete_from_organization(self.test_org.guid)
        self._assert_user_not_in_org(user, self.test_org.guid)

    @priority.low
    def test_admin_deletes_one_of_org_managers_cannot_delete_second(self):
        self.step("Add two managers to the organization")
        roles = User.ORG_ROLES["manager"]
        user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid, roles=roles)
        deleted_user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid, roles=roles)
        self.step("Remove one of the managers from the organization")
        deleted_user.api_delete_from_organization(org_guid=self.test_org.guid)
        self._assert_user_not_in_org(deleted_user, self.test_org.guid)
        self.step("Check that removing the last org manager returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            user.api_delete_from_organization, org_guid=self.test_org.guid)
        self.assert_user_in_org_and_roles(user, self.test_org.guid, roles)

    @priority.low
    def test_admin_updates_role_of_one_org_manager_cannot_delete_second(self):
        self.step("Add two users to the organization")
        manager_roles = User.ORG_ROLES["manager"]
        non_manager_roles = User.ORG_ROLES["auditor"]
        updated_user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                                 roles=manager_roles)
        manager = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                            roles=manager_roles)
        self.step("Update roles of one of the managers to non-manager")
        updated_user.api_update_org_roles(org_guid=self.test_org.guid, new_roles=non_manager_roles)
        self.assert_user_in_org_and_roles(updated_user, self.test_org.guid, non_manager_roles)
        self.step("Check that removing the last manger returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            manager.api_delete_from_organization, org_guid=self.test_org.guid)
        self.assert_user_in_org_and_roles(manager, self.test_org.guid, manager_roles)

    @priority.low
    def test_admin_cannot_delete_org_user_twice(self):
        self.step("Add test user to organization")
        user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                         roles=User.ORG_ROLES["auditor"])
        self.step("Delete test user from organization")
        user.api_delete_from_organization(org_guid=self.test_org.guid)
        self.step("Try to delete test user from organization second time")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY,
                                            user.api_delete_from_organization, org_guid=self.test_org.guid)

    @priority.low
    @pytest.mark.usefixtures("admin_user")
    def test_admin_cannot_delete_non_existing_org_user(self):
        self.step("Check that an attempt to delete user which is not in org returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY,
                                            test_data.TestData.admin_user.api_delete_from_organization,
                                            org_guid=self.test_org.guid)

    @priority.high
    def test_org_manager_can_delete_another_user(self):
        self.step("Add org manager to organization")
        user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                         roles=User.ORG_ROLES["manager"])
        user_client = user.login()
        deleted_user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                                 roles=User.ORG_ROLES["manager"])
        self.step("Org manager removes the user from the test org")
        deleted_user.api_delete_from_organization(org_guid=self.test_org.guid, client=user_client)
        self._assert_user_not_in_org(deleted_user, self.test_org.guid)

    @priority.low
    def test_non_manager_cannot_delete_user(self):
        self.step("Add org manager to organization")
        user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                         roles=User.ORG_ROLES["auditor"])
        user_client = user.login()
        deleted_user_roles = User.ORG_ROLES["billing_manager"]
        deleted_user = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                                 roles=deleted_user_roles)
        self.step("Check that non-manager cannot delete user from org")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            deleted_user.api_delete_from_organization, org_guid=self.test_org.guid,
                                            client=user_client)
        self.assert_user_in_org_and_roles(deleted_user, self.test_org.guid, deleted_user_roles)

