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
from modules.tap_object_model import Organization, User
from tests.fixtures import setup_fixtures, teardown_fixtures


@log_components(TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
@components(TAP.user_management)
class GetOrganizationUsers(TapTestCase):
    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Create users for org tests")
        users, cls.test_org = setup_fixtures.create_test_users(3)
        cls.step("Add manager role to user in the test org")
        cls.manager = users[0]
        cls.manager_client = users[0].login()
        cls.step("Add non-manager roles to users in the test org")
        cls.non_managers = {}
        cls.non_manager_clients = {}
        for index, roles in enumerate(cls.NON_MANAGER_ROLES):
            user = users[index + 1]
            user.api_update_org_roles(org_guid=cls.test_org.guid, new_roles=[roles])
            cls.non_managers[(roles,)] = user
            cls.non_manager_clients[roles] = user.login()

    @priority.low
    def test_non_manager_in_org_cannot_get_org_users(self):
        for role, client in self.non_manager_clients.items():
            with self.subTest(user_role=role):
                self.step("Check that non-manager cannot get list of users in org")
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    User.api_get_list_via_organization, org_guid=self.test_org.guid,
                                                    client=client)

    @priority.high
    def test_manager_can_get_org_users(self):
        self.step("Check that manager can get list of users in org")
        expected_users = [self.manager] + list(self.non_managers.values())
        user_list = User.api_get_list_via_organization(org_guid=self.test_org.guid, client=self.manager_client)
        self.assertUnorderedListEqual(user_list, expected_users)

    @priority.low
    def test_user_not_in_org_cannot_get_org_users(self):
        self.step("Create new org")
        org = Organization.api_create()
        self.step("Check that the user cannot get list of users in the test org")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            User.api_get_list_via_organization, org_guid=org.guid,
                                            client=self.manager_client)
