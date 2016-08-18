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
from modules.http_calls.platform import user_management
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import User
from tests.fixtures.assertions import assert_user_in_space_with_roles, assert_raises_http_exception

logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestUpdateSpaceUser:

    @priority.low
    def test_cannot_change_role_to_invalid_one(self, test_org, test_space, test_org_manager):
        initial_roles = User.SPACE_ROLES["manager"]
        new_roles = ("wrong_role",)
        step("Add user to space with roles {}".format(initial_roles))
        test_org_manager.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                          roles=initial_roles)
        step("Check that updating space user roles to invalid ones returns an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     test_org_manager.api_update_space_roles, test_space.guid,
                                     new_roles=new_roles)
        assert_user_in_space_with_roles(test_org_manager, test_space.guid)

    @priority.medium
    def test_cannot_delete_all_user_roles_while_in_space(self, test_org, test_space, test_org_manager):
        step("Add user to space")
        test_org_manager.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid)
        step("Try to update the user, removing all space roles")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_MUST_HAVE_AT_LEAST_ONE_ROLE,
                                     test_org_manager.api_update_space_roles, test_space.guid, new_roles=())
        assert_user_in_space_with_roles(test_org_manager, test_space.guid)

    @priority.high
    def test_change_user_role(self, test_org, test_space, test_org_manager):
        initial_roles = User.SPACE_ROLES["manager"]
        new_roles = User.SPACE_ROLES["auditor"]
        step("Add user to space with roles {}".format(initial_roles))
        test_org_manager.api_add_to_space(space_guid=test_space.guid, org_guid=test_org.guid,
                                          roles=initial_roles)
        step("Update the user, change their role to {}".format(new_roles))
        test_org_manager.api_update_space_roles(test_space.guid, new_roles=new_roles)
        assert_user_in_space_with_roles(test_org_manager, test_space.guid)

    @priority.low
    def test_cannot_update_non_existing_space_user(self, test_space):
        invalid_guid = "invalid-user-guid"
        roles = User.SPACE_ROLES["auditor"]
        step("Check that updating user which is not in space returns error")
        space_users = User.api_get_list_via_space(test_space.guid)
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                     user_management.api_update_space_user_roles, test_space.guid,
                                     invalid_guid, roles)
        users = User.api_get_list_via_space(test_space.guid)
        assert sorted(users) == sorted(space_users)

    @priority.low
    def test_cannot_update_space_user_in_not_existing_space(self, test_org_manager):
        invalid_guid = "invalid-space_guid"
        roles = User.SPACE_ROLES["auditor"]
        step("Check that updating user using invalid space guid return an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                     user_management.api_update_space_user_roles, invalid_guid,
                                     test_org_manager.guid, roles)

    @priority.low
    def test_send_space_role_update_request_with_empty_body(self, context, test_org, test_space):
        step("Create new platform user by adding to the space")
        test_user = User.api_create_by_adding_to_space(context, org_guid=test_org.guid,
                                                       space_guid=test_space.guid)
        step("Send request with empty body")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_MUST_HAVE_AT_LEAST_ONE_ROLE,
                                     user_management.api_update_space_user_roles, test_space.guid,
                                     test_user.guid)
        assert_user_in_space_with_roles(test_user, test_space.guid)
