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
from modules.tap_object_model import Organization, Space, User
from modules.test_names import get_test_name
from tests.fixtures import teardown_fixtures


class BaseTestClass(TapTestCase):
    ALL_SPACE_ROLES = {role for role_set in User.SPACE_ROLES.values() for role in role_set}

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.test_org = Organization.api_create()
        cls.test_user = User.api_create_by_adding_to_organization(cls.test_org.guid)

    def setUp(self):
        self.step("Create test space")
        self.test_space = Space.api_create(self.test_org)

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


@log_components()
@components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
class AddNewUserToSpace(BaseTestClass):

    def _get_test_user(self, org_guid, space_guid, space_role=User.ORG_ROLES["manager"]):
        return User.api_create_by_adding_to_space(org_guid, space_guid, roles=space_role)

    @priority.high
    def test_add_user_to_space(self):
        self.step("Create new platform user with each role by adding him to space")
        for space_role in self.ALL_SPACE_ROLES:
            with self.subTest(space_role=space_role):
                new_user = self._get_test_user(self.test_org.guid, self.test_space.guid, [space_role])
                self._assert_user_in_space_with_roles(new_user, self.test_space.guid)

    @priority.low
    def test_cannot_add_user_with_no_roles(self):
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_MUST_HAVE_AT_LEAST_ONE_ROLE,
                                            self._get_test_user, self.test_org.guid, self.test_space.guid, [])

    @priority.low
    def test_add_user_with_all_available_roles(self):
        self.step("Add user to space with roles {}".format(self.ALL_SPACE_ROLES))
        test_user = self._get_test_user(self.test_org.guid, self.test_space.guid, self.ALL_SPACE_ROLES)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    @priority.low
    def test_cannot_add_user_to_non_existing_space(self):
        space_guid = "this-space-guid-is-not-correct"
        self.step("Check that an error is raised when trying to add user using incorrect space guid")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            self._get_test_user, self.test_org.guid, space_guid)

    @priority.low
    def test_cannot_add_user_with_incorrect_role(self):
        space_users = User.api_get_list_via_space(self.test_space.guid)
        roles = ["i-don't-exist"]
        self.step("Check that error is raised when trying to add user using incorrect roles")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            User.api_create_by_adding_to_space, self.test_org.guid, self.test_space.guid,
                                            roles=roles)
        self.step("Assert user list did not change")
        self.assertListEqual(User.api_get_list_via_space(self.test_space.guid), space_users,
                             "User with incorrect roles was added to space")


@log_components()
@components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
class AddExistingUserToSpace(AddNewUserToSpace):

    def _get_test_user(self, org_guid, space_guid, space_role=User.ORG_ROLES["manager"]):
        self.step("Create new platform user by adding to the organization")
        test_user = User.api_create_by_adding_to_organization(org_guid)
        self.step("Add the user to space with role {}".format(space_role))
        test_user.api_add_to_space(space_guid, org_guid, roles=space_role)
        return test_user

    @priority.low
    def test_add_existing_user_by_updating_roles(self):
        user_not_in_space = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.step("Create test space")
        space = Space.api_create(self.test_org)
        self.step("Update user with a space role")
        user_not_in_space.api_update_space_roles(space.guid, new_roles=User.SPACE_ROLES["auditor"])
        self._assert_user_in_space_with_roles(user_not_in_space, space.guid)


@log_components()
@components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
class AddUserToSpace(BaseTestClass):
    @priority.low
    def test_cannot_create_new_user_with_long_username(self):
        """DPNG-5743 Adding a user with long username to space throws 500 while expected 400"""
        long_username = "x" * 300 + get_test_name(email=True)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMPTY,
                                            User.api_create_by_adding_to_space, self.test_org.guid,
                                            self.test_space.guid, username=long_username)

    @priority.low
    def test_cannot_create_new_user_with_non_email_username(self):
        non_email = "non_email_username"
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_space, self.test_org.guid,
                                            self.test_space.guid, username=non_email)

    @priority.medium
    def test_cannot_create_user_with_existing_username(self):
        test_user = User.api_create_by_adding_to_space(self.test_org.guid, self.test_space.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                            User.api_create_by_adding_to_space, self.test_org.guid,
                                            self.test_space.guid, username=test_user.username)

    @priority.low
    def test_cannot_create_user_with_special_characters_username(self):
        test_username = get_test_name(email=True)
        test_username = test_username.replace("@", "\n\t@")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_space, self.test_org.guid,
                                            self.test_space.guid, username=test_username)

    @priority.low
    def test_cannot_create_user_with_non_ascii_characters_username(self):
        test_username = get_test_name(email=True)
        test_username = "ąśćżźł" + test_username
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST,
                                            HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_space, self.test_org.guid,
                                            self.test_space.guid, username=test_username)
