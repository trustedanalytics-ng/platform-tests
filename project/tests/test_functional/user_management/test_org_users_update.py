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
from modules.tap_object_model import Organization, User
from tests.fixtures.assertions import assert_user_in_org_and_roles, assert_raises_http_exception

logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestUpdateOrganizationUser:

    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]
    ROLES_WITHOUT_MANAGER = [(name, user_role) for name, user_role in User.ORG_ROLES.items() if name is not "manager"]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def users(cls, test_org_manager, test_org_manager_client, class_context):
        step("Create test organization")
        cls.test_org = Organization.api_create(class_context)
        step("Create users for tests")
        cls.manager = User.api_create_by_adding_to_organization(class_context, org_guid=cls.test_org.guid,
                                                                roles=User.ORG_ROLES["manager"])
        cls.manager_client = cls.manager.login()
        cls.updated_user = User.api_create_by_adding_to_organization(class_context, org_guid=cls.test_org.guid, roles=[])

        cls.user_not_in_test_org = test_org_manager
        cls.client_not_in_test_org = test_org_manager_client

    @pytest.fixture(scope="function")
    def reset_updated_user(self, request):
        def fin():
            self.updated_user.api_update_org_roles(org_guid=self.test_org.guid, new_roles=[])
            self.manager.api_update_org_roles(org_guid=self.test_org.guid, new_roles=User.ORG_ROLES["manager"])
        request.addfinalizer(fin)

    @priority.high
    def test_update_org_user_roles(self, reset_updated_user):
        step("Add new role to the user, change it, and then remove")
        for updated_roles in [User.ORG_ROLES["auditor"], User.ORG_ROLES["billing_manager"], []]:
            self.updated_user.api_update_org_roles(self.test_org.guid, new_roles=updated_roles)
            assert_user_in_org_and_roles(self.updated_user, self.test_org.guid, updated_roles)

    @priority.low
    def test_remove_org_manager_role_from_the_only_org_manager(self):
        non_manager_roles = User.ORG_ROLES["auditor"]
        step("Remove manager role from the manager")
        self.manager.api_update_org_roles(org_guid=self.test_org.guid, new_roles=non_manager_roles)
        assert_user_in_org_and_roles(self.manager, self.test_org.guid, non_manager_roles)

    @priority.low
    def test_cannot_update_user_with_invalid_guid(self):
        # TODO implement non-existing guid
        step("Check that updating user which is not in an organization returns an error")
        invalid_guid = "invalid-user-guid"
        org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                     user_management.api_update_org_user_roles, org_guid=self.test_org.guid,
                                     user_guid=invalid_guid, new_roles=User.ORG_ROLES["billing_manager"])
        users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        assert sorted(users) == sorted(org_users)

    @priority.low
    def test_cannot_update_org_user_in_invalid_org_guid(self):
        # TODO implement non-existing guid
        invalid_guid = "invalid-org-guid"
        step("Check that updating user using invalid org guid returns an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                     user_management.api_update_org_user_roles, org_guid=invalid_guid,
                                     user_guid=self.updated_user.guid,
                                     new_roles=User.ORG_ROLES["billing_manager"])

    @priority.low
    def test_send_org_role_update_request_with_empty_body(self):
        step("Send request with empty body")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_CANNOT_PERFORM_REQ_WITHOUT_ROLES,
                                     user_management.api_update_org_user_roles, self.test_org.guid,
                                     self.updated_user.guid)

    @priority.low
    def test_cannot_update_org_user_with_incorrect_role(self, reset_updated_user):
        initial_roles = self.updated_user.org_roles.get(self.test_org.guid)
        invalid_roles = ["invalid role"]
        step("Check that updating user using invalid role returns an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     self.updated_user.api_update_org_roles, org_guid=self.test_org.guid,
                                     new_roles=invalid_roles)
        assert_user_in_org_and_roles(self.updated_user, self.test_org.guid, initial_roles)

    @priority.medium
    def test_manager_can_update_org_user(self, reset_updated_user):
        step("Check that org manager can update another user's roles")
        expected_roles = User.ORG_ROLES["manager"]
        self.updated_user.api_update_org_roles(org_guid=self.test_org.guid, new_roles=expected_roles,
                                               client=self.manager_client)
        assert_user_in_org_and_roles(self.updated_user, self.test_org.guid, expected_roles)

    @priority.medium
    def test_non_manager_cannot_update_org_user(self, context, reset_updated_user):
        step("Check that non-manager cannot update another user's roles")
        non_manager = User.api_create_by_adding_to_organization(context, org_guid=self.test_org.guid,
                                                                roles=self.NON_MANAGER_ROLES)
        non_manager_client = non_manager.login()
        org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     self.updated_user.api_update_org_roles, self.test_org.guid,
                                     new_roles=User.ORG_ROLES["auditor"], client=non_manager_client)
        users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        assert sorted(users) == sorted(org_users)

    @priority.low
    def test_user_cannot_update_user_in_org_where_they_are_not_added(self, reset_updated_user):
        step("Check that user not in org cannot update another user")
        expected_roles = self.updated_user.org_roles.get(self.test_org.guid, [])
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     self.updated_user.api_update_org_roles, self.test_org.guid,
                                     new_roles=User.ORG_ROLES["auditor"], client=self.client_not_in_test_org)
        assert_user_in_org_and_roles(self.updated_user, self.test_org.guid, expected_roles)

    @priority.low
    def test_cannot_update_user_which_is_not_in_org(self):
        step("Check that user not in org cannot be updated")
        org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        expected_message = HttpStatus.MSG_USER_NOT_EXIST_IN_ORGANIZATION.format(self.user_not_in_test_org.guid,
                                                                                self.test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, expected_message,
                                     self.user_not_in_test_org.api_update_org_roles, org_guid=self.test_org.guid,
                                     new_roles=User.ORG_ROLES["auditor"])
        users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        assert sorted(users) == sorted(org_users)
