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
from modules.markers import components, priority
from modules.tap_object_model import Organization, User
from tests.fixtures import fixtures


loged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [components.user_management]


class AddExistingUserToOrganization(TapTestCase):

    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def setup(cls, class_context):
        cls.step("Create test org")
        cls.test_org = Organization.api_create(class_context)
        cls.step("Add org manager")
        User.api_create_by_adding_to_organization(class_context, org_guid=cls.test_org.guid)

    @pytest.fixture(scope="function", autouse=True)
    def user(self, request, test_org_manager):
        self.test_user = test_org_manager

        def fin():
            fixtures.delete_or_not_found(self.test_user.api_delete_from_organization, org_guid=self.test_org.guid)
        request.addfinalizer(fin)

    @pytest.fixture(scope="function")
    def setup_context(self, context):
        # TODO move to methods when dependency on unittest is removed
        self.context = context

    def _assert_user_not_in_org(self, user, org_guid):
        # TODO refactor to fixtures.assertions
        self.step("Check that the user is not in the organization.")
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertNotIn(user, org_users, "User is among org users, although they shouldn't")

    @priority.medium
    def test_add_existing_user_with_no_roles(self):
        self.step("Add a platform user to organization with no roles.")
        expected_roles = []
        self.test_user.api_add_to_organization(org_guid=self.test_org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(self.test_user, self.test_org.guid, expected_roles)

    @priority.high
    def test_admin_adds_existing_user_one_role(self):
        # TODO parametrize
        expected_roles = User.ORG_ROLES["auditor"]
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        self.test_user.api_add_to_organization(self.test_org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(self.test_user, self.test_org.guid, expected_roles)

    @priority.low
    def test_admin_adds_existing_user_all_roles(self):
        self.step("Add a platform user to organization with all roles.")
        expected_roles = self.ALL_ROLES
        self.test_user.api_add_to_organization(self.test_org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(self.test_user, self.test_org.guid, expected_roles)

    @priority.low
    def test_admin_adds_user_which_is_already_in_org_with_the_same_role(self):
        expected_roles = User.ORG_ROLES["manager"]
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        self.test_user.api_add_to_organization(self.test_org.guid, roles=expected_roles)
        self.step("Add the same user to the same organization with the same roles")
        self.test_user.api_add_to_organization(self.test_org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(self.test_user, self.test_org.guid, expected_roles)

    @priority.low
    def test_admin_adds_user_which_is_already_in_org_with_different_role(self):
        roles_0 = User.ORG_ROLES["manager"]
        roles_1 = User.ORG_ROLES["auditor"]
        expected_roles = roles_0 | roles_1  # adding user with a new role results in the user having sum of the roles
        self.step("Add a platform user to organization with roles {}.".format(roles_0))
        self.test_user.api_add_to_organization(self.test_org.guid, roles=roles_0)
        self.step("Add the same user to the same organization with roles {}".format(roles_1))
        self.test_user.api_add_to_organization(self.test_org.guid, roles=roles_1)
        self.assert_user_in_org_and_roles(self.test_user, self.test_org.guid, expected_roles)

    @priority.medium
    @pytest.mark.usefixtures("setup_context")
    def test_org_manager_adds_existing_user(self):
        self.step("Add a manager to the organization.")
        org_manager = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                                roles=User.ORG_ROLES["manager"])
        manager_client = org_manager.login()
        expected_roles = User.ORG_ROLES["auditor"]
        self.step("The new manager adds a platform user to the organization.")
        self.test_user.api_add_to_organization(self.test_org.guid, roles=expected_roles, client=manager_client)
        self.assert_user_in_org_and_roles(self.test_user, self.test_org.guid, expected_roles)

    @priority.medium
    @pytest.mark.usefixtures("setup_context")
    def test_non_manager_cannot_add_existing_user_to_org(self):
        self.step("Add a non-manager to the organization.")
        non_manager = User.api_create_by_adding_to_organization(self.context, org_guid=self.test_org.guid,
                                                                roles=User.ORG_ROLES["auditor"])
        non_manager_client = non_manager.login()
        self.step("Check that the non-manager is able to add a platform user to the org")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            self.test_user.api_add_to_organization, org_guid=self.test_org.guid,
                                            roles=User.ORG_ROLES["auditor"], client=non_manager_client)
        self._assert_user_not_in_org(self.test_user, self.test_org.guid)

    @priority.medium
    def test_user_cannot_add_themselves_to_org(self):
        test_client = self.test_user.login()
        self.step("Check that a platform user is not able to add themselves to the organization")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            self.test_user.api_add_to_organization, org_guid=self.test_org.guid,
                                            roles=User.ORG_ROLES["auditor"], client=test_client)
        self._assert_user_not_in_org(self.test_user, self.test_org.guid)

    @priority.low
    def test_cannot_add_existing_user_to_non_existing_org(self):
        self.step("Check that adding user to organization using invalid org guid raises an error")
        invalid_org_guid = "this-org-guid-is-not-correct"
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            self.test_user.api_add_to_organization, org_guid=invalid_org_guid,
                                            roles=self.ALL_ROLES)

    @priority.low
    def test_cannot_add_existing_user_with_incorrect_role(self):
        self.step("Check that it is not possible to add user to the organization with incorrect role.")
        invalid_role = ["incorrect-role"]
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            self.test_user.api_add_to_organization, org_guid=self.test_org.guid,
                                            roles=invalid_role)
        self._assert_user_not_in_org(self.test_user, self.test_org.guid)
