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
from modules.tap_object_model import Space, User
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from tests.fixtures.test_data import TestData


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [components.user_management, components.auth_gateway, components.auth_proxy]


class DeleteSpaceUser(TapTestCase):

    @pytest.fixture(scope="function", autouse=True)
    def space(self, request, test_org, test_org_manager):
        self.step("Create test space")
        self.test_space = Space.api_create(test_org)

        def fin():
            self.test_space.cleanup()
        request.addfinalizer(fin)

    @priority.high
    def test_delete_user_from_space(self):
        self.step("Add the user to space")
        TestData.test_org_manager.api_add_to_space(self.test_space.guid, TestData.test_org.guid)
        self.step("Delete the user from space")
        TestData.test_org_manager.api_delete_from_space(self.test_space.guid)
        self.assertNotInWithRetry(TestData.test_org_manager, User.api_get_list_via_space, self.test_space.guid)
        self.step("Check that the user is still in the organization")
        org_users = User.api_get_list_via_organization(org_guid=TestData.test_org.guid)
        self.assertIn(TestData.test_org_manager, org_users, "User is not in the organization")

    @priority.low
    def test_delete_user_which_is_not_in_space(self):
        self.step("Check that deleting the user from space they are not in returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_USER_IS_NOT_IN_GIVEN_SPACE,
                                            TestData.test_org_manager.api_delete_from_space, self.test_space.guid)
