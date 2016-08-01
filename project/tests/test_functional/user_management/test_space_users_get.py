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
from modules.markers import priority
from modules.tap_object_model import Space, User
from tests.fixtures.test_data import TestData


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class GetSpaceUsers(TapTestCase):

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def space_and_users(cls, request, test_org, class_context):
        cls.test_space = Space.api_create(org=test_org)
        cls.test_users = [User.api_create_by_adding_to_organization(class_context, org_guid=test_org.guid)
                          for _ in range(2)]

    def test_get_user_list_from_space(self):
        self.step("Check that space is empty")
        self.assertEqual([], User.api_get_list_via_space(self.test_space.guid), "List is not empty")
        self.step("Add users to space")
        for user in self.test_users:
            user.api_add_to_space(self.test_space.guid, TestData.test_org.guid)
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertListEqual(self.test_users, space_user_list)

    @priority.low
    def test_cannot_get_user_list_from_deleted_space(self):
        self.step("Create and delete the space")
        deleted_space = Space.api_create(TestData.test_org)
        deleted_space.cleanup()
        self.step("Check that retrieving list of users in the deleted space returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                            User.api_get_list_via_space, deleted_space.guid)
