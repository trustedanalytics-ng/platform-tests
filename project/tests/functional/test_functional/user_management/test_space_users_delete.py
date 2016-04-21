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
from modules.tap_object_model import Organization, Space, User
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, priority


@log_components()
@components(TAP.user_management)
class DeleteSpaceUser(TapTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, User.cf_api_tear_down_test_users)
    def setUpClass(cls):
        cls.test_org = Organization.api_create()
        cls.test_user = User.api_create_by_adding_to_organization(cls.test_org.guid)

    def setUp(self):
        self.step("Create test space")
        self.test_space = Space.api_create(self.test_org)

    @priority.high
    def test_delete_user_from_space(self):
        self.step("Add the user to space")
        self.test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        self.step("Delete the user from space")
        self.test_user.api_delete_from_space(self.test_space.guid)
        self.assertNotInWithRetry(self.test_user, User.api_get_list_via_space, self.test_space.guid)
        self.step("Check that the user is still in the organization")
        org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        self.assertIn(self.test_user, org_users, "User is not in the organization")

    @priority.low
    def test_delete_user_which_is_not_in_space(self):
        self.step("Check that deleting the user from space they are not in returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_USER_IS_NOT_IN_GIVEN_SPACE,
                                            self.test_user.api_delete_from_space, self.test_space.guid)
