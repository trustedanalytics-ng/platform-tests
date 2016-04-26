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
from modules.api_client import PlatformApiClient
from modules.remote_logger.remote_logger_decorator import log_components
from modules.tap_object_model import Organization, Space, User
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, priority


@log_components()
@components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
class SpaceUserPermissions(TapTestCase):
    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.client_permission = {
            "admin": True,
            "org_manager": True,
            "space_manager_in_org": True,
            "org_user": False,
            "other_org_manager": False,
            "other_user": False
        }
        cls.test_org = Organization.api_create()
        cls.test_space = Space.api_create(cls.test_org)
        cls.users_clients = cls._get_user_clients(cls.test_org.guid, cls.test_space.guid)

    @staticmethod
    def _get_user_clients(org_guid, space_guid):
        other_test_org = Organization.api_create()
        return {"admin": PlatformApiClient.get_admin_client(),
                "org_manager": User.api_create_by_adding_to_organization(org_guid).login(),
                "space_manager_in_org": User.api_create_by_adding_to_space(org_guid, space_guid).login(),
                "org_user": User.api_create_by_adding_to_organization(org_guid, 
                                                                      roles=User.ORG_ROLES["auditor"]).login(),
                "other_org_manager": User.api_create_by_adding_to_organization(other_test_org.guid).login(),
                "other_user": User.api_create_by_adding_to_organization(other_test_org.guid, roles=[]).login()}

    def _assert_user_in_space_with_roles(self, expected_user, space_guid):
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
        test_user = User.api_create_by_adding_to_space(self.test_org.guid, self.test_space.guid)
        self.step("Try to get user list from space by using every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                if is_authorized:
                    user_list = User.api_get_list_via_space(self.test_space.guid, client=self.users_clients[client])
                    self.assertIn(test_user, user_list, "User {} was not found in list".format(test_user))
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        User.api_get_list_via_space, self.test_space.guid,
                                                        client=self.users_clients[client])

    @priority.medium
    def test_add_new_user(self):
        self.step("Try to add new user with every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                user_list = User.api_get_list_via_space(self.test_space.guid)
                if is_authorized:
                    test_user = User.api_create_by_adding_to_space(self.test_org.guid, self.test_space.guid,
                                                                   inviting_client=self.users_clients[client])
                    self._assert_user_in_space_with_roles(test_user, self.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        User.api_create_by_adding_to_space, self.test_org.guid,
                                                        self.test_space.guid,
                                                        inviting_client=self.users_clients[client])
                    self.assertUnorderedListEqual(User.api_get_list_via_space(self.test_space.guid), user_list,
                                                  "User was added")

    @priority.medium
    def test_add_existing_user(self):
        self.step("Try to add existing user to space with every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                if is_authorized:
                    test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
                    test_user.api_add_to_space(self.test_space.guid, self.test_org.guid,
                                               client=self.users_clients[client])
                    self._assert_user_in_space_with_roles(test_user, self.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        User.api_create_by_adding_to_space, self.test_org.guid,
                                                        self.test_space.guid, inviting_client=self.users_clients[client])

    @priority.medium
    def test_update_role(self):
        new_roles = User.SPACE_ROLES["auditor"]
        self.step("Try to change user space role using every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(userType=client):
                test_user = User.api_create_by_adding_to_space(self.test_org.guid, self.test_space.guid,
                                                               roles=User.SPACE_ROLES["developer"])
                if is_authorized:
                    test_user.api_update_space_roles(self.test_space.guid, new_roles=new_roles,
                                                     client=self.users_clients[client])
                    self._assert_user_in_space_with_roles(test_user, self.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        test_user.api_update_space_roles, self.test_space.guid,
                                                        new_roles=new_roles, client=self.users_clients[client])
                    self.assertListEqual(test_user.space_roles.get(self.test_space.guid),
                                         list(User.SPACE_ROLES["developer"]), "User roles were updated")

    @priority.medium
    def test_delete_user(self):
        self.step("Try to delete user from space using every client type")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(userType=client):
                test_user = User.api_create_by_adding_to_space(self.test_org.guid, self.test_space.guid)
                self._assert_user_in_space_with_roles(test_user, self.test_space.guid)
                if is_authorized:
                    test_user.api_delete_from_space(self.test_space.guid, client=self.users_clients[client])
                    self.assertNotInWithRetry(test_user, User.api_get_list_via_space, self.test_space.guid)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        test_user.api_delete_from_space, self.test_space.guid,
                                                        client=self.users_clients[client])
                    self.assertIn(test_user, User.api_get_list_via_space(self.test_space.guid), "User was deleted")

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
        for client in self.users_clients:
            with self.subTest(userType=client):
                space_list = self.test_org.api_get_spaces()
                if client_permission[client]:
                    new_space = Space.api_create(self.test_org, client=self.users_clients[client])
                    space_list = Space.api_get_list()
                    self.assertIn(new_space, space_list, "Space was not created.")
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        Space.api_create, self.test_org,
                                                        client=self.users_clients[client])
                    self.assertUnorderedListEqual(self.test_org.api_get_spaces(), space_list, "Space was created")

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
        for client in self.users_clients:
            with self.subTest(userType=client):
                new_space = Space.api_create(self.test_org)
                if client_permission[client]:
                    new_space.api_delete(client=self.users_clients[client])
                    self.assertNotInWithRetry(new_space, Space.api_get_list)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        new_space.api_delete, client=self.users_clients[client])
                    self.assertIn(new_space, self.test_org.api_get_spaces(), "Space was not deleted")

