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
from modules.tap_object_model import Space, User
from tests.fixtures import setup_fixtures, teardown_fixtures


@log_components()
@components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
class GetSpaceUsers(TapTestCase):
    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.test_users, cls.test_org = setup_fixtures.create_test_users(3)
        cls.test_space = Space.api_create(cls.test_org)

    def test_get_user_list_from_space(self):
        self.step("Check that space is empty")
        self.assertEqual([], User.api_get_list_via_space(self.test_space.guid), "List is not empty")
        self.step("Add users to space")
        for user in self.test_users:
            user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertListEqual(self.test_users, space_user_list)

    @priority.low
    def test_cannot_get_user_list_from_deleted_space(self):
        self.step("Create and delete the space")
        deleted_space = Space.api_create(self.test_org)
        deleted_space.cf_api_delete()
        self.step("Check that retrieving list of users in the deleted space returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_NOT_FOUND,
                                            User.api_get_list_via_space, deleted_space.guid)

