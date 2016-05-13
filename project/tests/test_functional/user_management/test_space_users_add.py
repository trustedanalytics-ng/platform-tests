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
from modules.tap_object_model import Space, User
from modules.test_names import generate_test_object_name
from tests.fixtures import fixtures


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)


class BaseTestClass(TapTestCase):
    ALL_SPACE_ROLES = {role for role_set in User.SPACE_ROLES.values() for role in role_set}

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def space(cls, request, test_org, test_org_manager):
        cls.test_org = test_org
        cls.test_user = test_org_manager
        cls.step("Create test space")
        cls.test_space = Space.api_create(cls.test_org)

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


class AddNewUserToSpace(BaseTestClass):
    pytestmark = [components.auth_gateway, components.auth_proxy, components.user_management]

    def _get_test_user(self, org_guid, space_guid, space_role=User.ORG_ROLES["manager"]):
        user = User.api_create_by_adding_to_space(self.context, org_guid, space_guid, roles=space_role)
        return user

    @pytest.fixture(scope="function", autouse=True)
    def setup_context(self, context):
        # TODO move to methods when dependency on unittest is removed
        self.context = context

    @priority.high
    def test_add_user_to_space(self):
        # TODO parametrize
        self.step("Create new platform user with each role by adding them to space")
        new_user = self._get_test_user(self.test_org.guid, self.test_space.guid, User.SPACE_ROLES["manager"])
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
                                            User.api_create_by_adding_to_space, self.context, self.test_org.guid,
                                            self.test_space.guid, roles=roles)
        self.step("Assert user list did not change")
        self.assertListEqual(User.api_get_list_via_space(self.test_space.guid), space_users,
                             "User with incorrect roles was added to space")


class AddExistingUserToSpace(AddNewUserToSpace):
    pytestmark = [components.user_management]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def user(cls, request, test_org, class_context):
        cls.step("Create new platform user by adding to the organization")
        cls.test_user = User.api_create_by_adding_to_organization(class_context, test_org.guid)

    @pytest.fixture(scope="function", autouse=True)
    def cleanup(self, request):
        def fin():
            fixtures.delete_or_not_found(self.test_user.api_delete_from_space, space_guid=self.test_space.guid)
        request.addfinalizer(fin)

    def _get_test_user(self, org_guid, space_guid, space_role=User.ORG_ROLES["manager"]):
        self.step("Add the user to space with role {}".format(space_role))
        self.test_user.api_add_to_space(space_guid, org_guid, roles=space_role)
        return self.test_user

    @priority.low
    def test_add_existing_user_by_updating_roles(self):
        self.step("Update user with a space role")
        self.test_user.api_update_space_roles(self.test_space.guid, new_roles=User.SPACE_ROLES["auditor"])
        self._assert_user_in_space_with_roles(self.test_user, self.test_space.guid)


class AddUserToSpace(TapTestCase):
    pytestmark = [components.user_management]

    @pytest.fixture(scope="function", autouse=True)
    def setup_context(self, context):
        # TODO move to methods when dependency on unittest is removed
        self.context = context

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def space(cls, request, test_org):
        cls.test_org = test_org
        cls.step("Create test space")
        cls.test_space = Space.api_create(cls.test_org)
        request.addfinalizer(lambda: fixtures.delete_or_not_found(cls.test_space.api_delete))

    @priority.low
    @pytest.mark.bugs("DPNG-5743 Adding a user with long username to space throws 500 while expected 400")
    def test_cannot_create_new_user_with_long_username(self):
        long_username = "x" * 300 + generate_test_object_name(email=True)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMPTY,
                                            User.api_create_by_adding_to_space, self.context, self.test_org.guid,
                                            self.test_space.guid, username=long_username)

    @priority.low
    def test_cannot_create_new_user_with_non_email_username(self):
        non_email = "non_email_username"
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_space, self.context, self.test_org.guid,
                                            self.test_space.guid, username=non_email)

    @priority.medium
    def test_cannot_create_user_with_existing_username(self):
        test_user = User.api_create_by_adding_to_space(self.context, self.test_org.guid, self.test_space.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                            User.api_create_by_adding_to_space, self.context, self.test_org.guid,
                                            self.test_space.guid, username=test_user.username)

    @priority.low
    def test_cannot_create_user_with_special_characters_username(self):
        test_username = generate_test_object_name(email=True)
        test_username = test_username.replace("@", "\n\t@")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_space, self.context, self.test_org.guid,
                                            self.test_space.guid, username=test_username)

    @priority.low
    def test_cannot_create_user_with_non_ascii_characters_username(self):
        test_username = generate_test_object_name(email=True)
        test_username = "ąśćżźł" + test_username
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST,
                                            HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_space, self.context, self.test_org.guid,
                                            self.test_space.guid, username=test_username)
