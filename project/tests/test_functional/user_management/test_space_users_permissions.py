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

from modules.api_client import PlatformApiClient
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.markers import components, priority
from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import Organization, Space, User
from tests.fixtures.test_data import TestData


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [components.user_management]


class SpaceUserPermissions(TapTestCase):

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def user_clients(cls, request, test_org, test_space, class_context):
        cls.context = class_context  # TODO move to methods when dependency on unittest is removed
        cls.client_permission = {
            "admin": True,
            "org_manager": True,
            "space_manager_in_org": True,
            "org_user": False,
            "other_org_manager": False,
            "other_user": False
        }
        second_test_org = Organization.api_create(class_context)
        org_manager = User.api_create_by_adding_to_organization(class_context, test_org.guid)
        space_manager_in_org = User.api_create_by_adding_to_space(class_context, test_org.guid, test_space.guid)
        org_user = User.api_create_by_adding_to_organization(class_context, test_org.guid,
                                                             roles=User.ORG_ROLES["auditor"])
        other_org_manager = User.api_create_by_adding_to_organization(class_context, second_test_org.guid)
        other_user = User.api_create_by_adding_to_organization(class_context, second_test_org.guid, roles=[])
        cls.user_clients = {
            "admin": PlatformApiClient.get_admin_client(),
            "org_manager": org_manager.login(),
            "space_manager_in_org": space_manager_in_org.login(),
            "org_user": org_user.login(),
            "other_org_manager": other_org_manager.login(),
            "other_user": other_user.login()
        }

    def _assert_user_in_space_with_roles(self, expected_user, space_guid):
        # TODO move to TapTestCase
        self.step("Check that the user is on the list of space users")
        space_users = User.api_get_list_via_space(space_guid)
        self.assertIn(expected_user, space_users)
        space_user = next(user for user in space_users if user.guid == expected_user.guid)
        self.step("Check that the user has expected space roles")
        space_user_roles = space_user.space_roles.get(space_guid)
        expected_roles = expected_user.space_roles.get(space_guid)
        self.assertUnorderedListEqual(space_user_roles, expected_roles,
                                      "{} space roles are not equal".format(expected_user))

    @priority.medium
    def test_get_user_list(self):
        test_user = User.api_create_by_adding_to_space(self.context, TestData.test_org.guid, TestData.test_space.guid)
        self.step("Try to get user list from space by using every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                if is_authorized:
                    user_list = User.api_get_list_via_space(TestData.test_space.guid, client=self.user_clients[client])
                    self.assertIn(test_user, user_list, "User {} was not found in list".format(test_user))
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        User.api_get_list_via_space, TestData.test_space.guid,
                                                        client=self.user_clients[client])

    @priority.medium
    def test_add_new_user(self):
        self.step("Try to add new user with each client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                user_list = User.api_get_list_via_space(TestData.test_space.guid)
                if is_authorized:
                    test_user = User.api_create_by_adding_to_space(self.context, TestData.test_org.guid,
                                                                   TestData.test_space.guid,
                                                                   inviting_client=self.user_clients[client])
                    self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        User.api_create_by_adding_to_space, self.context,
                                                        TestData.test_org.guid, TestData.test_space.guid,
                                                        inviting_client=self.user_clients[client])
                    self.assertUnorderedListEqual(User.api_get_list_via_space(TestData.test_space.guid), user_list,
                                                  "User was added")

    @priority.medium
    def test_add_existing_user(self):
        self.step("Try to add existing user to space with every client type.")
        test_user = User.api_create_by_adding_to_organization(self.context, TestData.test_org.guid)
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                if is_authorized:
                    test_user.api_add_to_space(TestData.test_space.guid, TestData.test_org.guid,
                                               client=self.user_clients[client])
                    self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        User.api_create_by_adding_to_space, self.context,
                                                        TestData.test_org.guid, TestData.test_space.guid,
                                                        inviting_client=self.user_clients[client])

    @priority.medium
    def test_update_role(self):
        new_roles = User.SPACE_ROLES["auditor"]
        self.step("Try to change user space role using every client type.")
        test_user = User.api_create_by_adding_to_organization(self.context, TestData.test_org.guid)
        for client, is_authorized in self.client_permission.items():
            with self.subTest(userType=client):
                if is_authorized:
                    test_user.api_update_space_roles(TestData.test_space.guid, new_roles=new_roles,
                                                     client=self.user_clients[client])
                    self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        test_user.api_update_space_roles, TestData.test_space.guid,
                                                        new_roles=new_roles, client=self.user_clients[client])

    @priority.medium
    def test_delete_user(self):
        test_user = User.api_create_by_adding_to_organization(self.context, TestData.test_org.guid)
        self.step("Try to delete user from space using every client type")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(userType=client):
                test_user.api_add_to_space(org_guid=TestData.test_org.guid, space_guid=TestData.test_space.guid)
                self._assert_user_in_space_with_roles(test_user, TestData.test_space.guid)
                if is_authorized:
                    test_user.api_delete_from_space(TestData.test_space.guid, client=self.user_clients[client])
                    self.assertNotInWithRetry(test_user, User.api_get_list_via_space, TestData.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        test_user.api_delete_from_space, TestData.test_space.guid,
                                                        client=self.user_clients[client])
                    self.assertIn(test_user, User.api_get_list_via_space(TestData.test_space.guid),
                                  "User was deleted")

    @priority.medium
    def test_add_space(self):
        client_permission = {
            "admin": True,
            "org_manager": True,
            "space_manager_in_org": False,
            "org_user": False,
            "other_org_manager": False,
            "other_user": False
        }
        self.step("Try to add new space using every client type.")
        for client in self.user_clients:
            with self.subTest(userType=client):
                space_list = Space.api_get_list_in_org(org_guid=TestData.test_org.guid)
                if client_permission[client]:
                    new_space = Space.api_create(TestData.test_org, client=self.user_clients[client])
                    space_list = Space.api_get_list()
                    self.assertIn(new_space, space_list, "Space was not created.")
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        Space.api_create, TestData.test_org,
                                                        client=self.user_clients[client])
                    self.assertUnorderedListEqual(Space.api_get_list_in_org(org_guid=TestData.test_org.guid),
                                                  space_list, "Space was created")

    @priority.medium
    def test_delete_space(self):
        client_permission = {
            "admin": True,
            "org_manager": True,
            "space_manager_in_org": False,
            "org_user": False,
            "other_org_manager": False,
            "other_user": False
        }
        self.step("Try to delete space using every client type.")
        for client in self.user_clients:
            with self.subTest(userType=client):
                new_space = Space.api_create(TestData.test_org)
                if client_permission[client]:
                    new_space.api_delete(client=self.user_clients[client])
                    self.assertNotInWithRetry(new_space, Space.api_get_list)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        new_space.api_delete, client=self.user_clients[client])
                    self.assertIn(new_space, Space.api_get_list_in_org(org_guid=TestData.test_org.guid),
                                  "Space was not deleted")

