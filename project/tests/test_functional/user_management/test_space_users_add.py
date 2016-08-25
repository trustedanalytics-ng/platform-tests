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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import User
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception, assert_user_in_space_with_roles
from config import tap_type
from config import TapType

logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
tap_ng = TapType.tap_ng.value


@pytest.mark.skipif(tap_type == tap_ng, reason="Spaces are not predicted for TAP_NG")
class TestAddNewUserToSpace:
    pytestmark = [pytest.mark.components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)]
    ALL_SPACE_ROLES = {role for role_set in User.SPACE_ROLES.values() for role in role_set}

    @staticmethod
    def _get_test_user(context, org_guid, space_guid, space_role=User.ORG_ROLES["manager"]):
        user = User.api_create_by_adding_to_space(context, org_guid, space_guid, roles=space_role)
        return user

    @priority.high
    @pytest.mark.parametrize("space_role", ["manager", "auditor", "developer"])
    def test_add_user_to_space(self, context, test_org, test_space, space_role):
        step("Create new platform user with each role by adding them to space")
        new_user = self._get_test_user(context, test_org.guid, test_space.guid, User.SPACE_ROLES[space_role])
        assert_user_in_space_with_roles(new_user, test_space.guid)

    @priority.low
    def test_cannot_add_user_with_no_roles(self, context, test_org, test_space):
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_MUST_HAVE_AT_LEAST_ONE_ROLE,
                                     self._get_test_user, context, test_org.guid, test_space.guid, [])

    @priority.low
    def test_add_user_with_all_available_roles(self, context, test_org, test_space):
        step("Add user to space with roles {}".format(self.ALL_SPACE_ROLES))
        test_user = self._get_test_user(context, test_org.guid, test_space.guid, self.ALL_SPACE_ROLES)
        assert_user_in_space_with_roles(test_user, test_space.guid)

    @priority.low
    def test_cannot_add_user_to_non_existing_space(self, context, test_org):
        space_guid = "this-space-guid-is-not-correct"
        step("Check that an error is raised when trying to add user using incorrect space guid")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                     self._get_test_user, context, test_org.guid, space_guid)

    @priority.low
    def test_cannot_add_user_with_incorrect_role(self, context, test_org, test_space):
        space_users = User.api_get_list_via_space(test_space.guid)
        roles = ["i-don't-exist"]
        step("Check that error is raised when trying to add user using incorrect roles")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     User.api_create_by_adding_to_space, context, test_org.guid,
                                     test_space.guid, roles=roles)
        step("Assert user list did not change")
        users = User.api_get_list_via_space(test_space.guid)
        assert sorted(users) == sorted(space_users), "User with incorrect roles was added to space"

    @priority.low
    def test_add_existing_user_by_updating_roles(self, test_space, test_org_manager):
        step("Update user with a space role")
        test_org_manager.api_update_space_roles(test_space.guid, new_roles=User.SPACE_ROLES["auditor"])
        assert_user_in_space_with_roles(test_org_manager, test_space.guid)


@pytest.mark.skipif(tap_type == tap_ng, reason="Spaces are not predicted for TAP_NG")
class TestAddUserToSpace:
    pytestmark = [pytest.mark.components(TAP.user_management)]

    @priority.low
    @pytest.mark.bugs("DPNG-5743 Adding a user with long username to space throws 500 while expected 400")
    def test_cannot_create_new_user_with_long_username(self, context, test_org, test_space):
        long_username = "x" * 300 + generate_test_object_name(email=True)
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMPTY,
                                     User.api_create_by_adding_to_space, context, test_org.guid,
                                     test_space.guid, username=long_username)

    @priority.low
    def test_cannot_create_new_user_with_non_email_username(self, context, test_org, test_space):
        non_email = "non_email_username"
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                     User.api_create_by_adding_to_space, context, test_org.guid,
                                     test_space.guid, username=non_email)

    @priority.medium
    def test_cannot_create_user_with_existing_username(self, context, test_org, test_space):
        test_user = User.api_create_by_adding_to_space(context, test_org.guid, test_space.guid)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                     User.api_create_by_adding_to_space, context, test_org.guid,
                                     test_space.guid, username=test_user.username)

    @priority.low
    def test_cannot_create_user_with_special_characters_username(self, context, test_org, test_space):
        test_username = generate_test_object_name(email=True)
        test_username = test_username.replace("@", "\n\t@")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                     User.api_create_by_adding_to_space, context, test_org.guid,
                                     test_space.guid, username=test_username)

    @priority.low
    def test_cannot_create_user_with_non_ascii_characters_username(self, context, test_org, test_space):
        test_username = generate_test_object_name(email=True)
        test_username = "ąśćżźł" + test_username
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST,
                                     HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                     User.api_create_by_adding_to_space, context, test_org.guid,
                                     test_space.guid, username=test_username)
