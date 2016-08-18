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
from modules.tap_logger import step
from modules.tap_object_model import Space, User
from modules.markers import priority
from tests.fixtures.assertions import assert_not_in_with_retry, assert_raises_http_exception


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)]


class TestDeleteSpaceUser:

    @priority.high
    def test_delete_user_from_space(self, test_org, test_space, test_org_manager):
        step("Add the user to space")
        test_org_manager.api_add_to_space(test_space.guid, test_org.guid)
        step("Delete the user from space")
        test_org_manager.api_delete_from_space(test_space.guid)
        assert_not_in_with_retry(test_org_manager, User.api_get_list_via_space, test_space.guid)
        step("Check that the user is still in the organization")
        org_users = User.api_get_list_via_organization(org_guid=test_org.guid)
        assert test_org_manager in org_users, "User is not in the organization"

    @priority.low
    def test_delete_user_which_is_not_in_space(self, test_space, test_org_manager):
        step("Check that deleting the user from space they are not in returns an error")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_USER_IS_NOT_IN_GIVEN_SPACE,
                                     test_org_manager.api_delete_from_space, test_space.guid)
