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
from modules.http_calls import platform as api
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, priority
from modules.tap_object_model import Organization, Space, User
from tests.fixtures import teardown_fixtures


@log_components()
@components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
class UpdateSpaceUser(TapTestCase):

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

    @priority.high
    def test_change_user_role(self):
        initial_roles = User.SPACE_ROLES["manager"]
        new_roles = User.SPACE_ROLES["auditor"]
        self.step("Add user to space with roles {}".format(initial_roles))
        self.test_user.api_add_to_space(space_guid=self.test_space.guid, org_guid=self.test_org.guid, roles=initial_roles)
        self.step("Update the user, change their role to {}".format(new_roles))
        self.test_user.api_update_space_roles(self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(self.test_user, self.test_space.guid)

    @priority.low
    def test_cannot_change_role_to_invalid_one(self):
        initial_roles = User.SPACE_ROLES["manager"]
        new_roles = ("wrong_role",)
        self.step("Add user to space with roles {}".format(initial_roles))
        self.test_user.api_add_to_space(space_guid=self.test_space.guid, org_guid=self.test_org.guid, roles=initial_roles)
        self.step("Check that updating space user roles to invalid ones returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            self.test_user.api_update_space_roles, self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(self.test_user, self.test_space.guid)

    @priority.medium
    def test_cannot_delete_all_user_roles_while_in_space(self):
        self.step("Add user to space")
        self.test_user.api_add_to_space(space_guid=self.test_space.guid, org_guid=self.test_org.guid)
        self.step("Try to update the user, removing all space roles")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_MUST_HAVE_AT_LEAST_ONE_ROLE,
                                            self.test_user.api_update_space_roles, self.test_space.guid, new_roles=())
        self._assert_user_in_space_with_roles(self.test_user, self.test_space.guid)

    @priority.low
    def test_cannot_update_non_existing_space_user(self):
        invalid_guid = "invalid-user-guid"
        roles = User.SPACE_ROLES["auditor"]
        self.step("Check that updating user which is not in space returns error")
        space_users = User.api_get_list_via_space(self.test_space.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            api.api_update_space_user_roles, self.test_space.guid, invalid_guid, roles)
        self.assertListEqual(User.api_get_list_via_space(self.test_space.guid), space_users)

    @priority.low
    def test_cannot_update_space_user_in_not_existing_space(self):
        invalid_guid = "invalid-space_guid"
        roles = User.SPACE_ROLES["auditor"]
        self.step("Check that updating user using invalid space guid return an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            api.api_update_space_user_roles, invalid_guid, self.test_user.guid, roles)

    @priority.low
    def test_send_space_role_update_request_with_empty_body(self):
        self.step("Create new platform user by adding to the space")
        test_user = User.api_create_by_adding_to_space(org_guid=self.test_org.guid, space_guid=self.test_space.guid)
        self.step("Send request with empty body")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_MUST_HAVE_AT_LEAST_ONE_ROLE,
                                            api.api_update_space_user_roles, self.test_space.guid, test_user.guid)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)
