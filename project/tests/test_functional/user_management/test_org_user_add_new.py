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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import User
from tests.fixtures.assertions import assert_user_in_org_and_role, assert_raises_http_exception

logged_components = (TAP.user_management, TAP.auth_gateway)
pytestmark = [pytest.mark.components(TAP.user_management, TAP.auth_gateway)]


class TestAddNewUserToOrganization:

    @pytest.fixture(scope="class")
    def add_user_test_cases(self):
        return {
            "add_admin": {"sent": User.ORG_ROLE["admin"], "expected": User.ORG_ROLE["admin"]},
            "add_user": {"sent": User.ORG_ROLE["user"], "expected": User.ORG_ROLE["user"]},
            "add_None": {"sent": None, "expected": User.ORG_ROLE["user"]}
        }

    @priority.medium
    @pytest.mark.parametrize("test_case", ("add_admin", "add_user", "add_None"))
    def test_add_new_user_with_no_roles(self, context, test_org, test_case, add_user_test_cases):
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        role_sent = add_user_test_cases[test_case]["sent"]
        role_expected = add_user_test_cases[test_case]["expected"]
        step("Create new user by adding to an organization with role {}".format(role_sent))
        user = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid, role=role_sent)
        step("Check that the user was added with role {}".format(role_expected))
        assert_user_in_org_and_role(user, test_org.guid, role_expected)

    @priority.high
    @pytest.mark.parametrize("test_case", ("add_admin", "add_user", "add_None"))
    def test_platform_admin_adds_new_user_in_org_where_they_are_not_added(self, context, admin_user, test_org,
                                                                          test_case, add_user_test_cases,
                                                                          remove_admin_from_test_org):
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        role_sent = add_user_test_cases[test_case]["sent"]
        role_expected = add_user_test_cases[test_case]["expected"]
        step("Create new user by adding them to an organization with user role")
        new_user = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid, role=role_sent)
        step("Check that the user was added with user role")
        assert_user_in_org_and_role(new_user, test_org.guid, role_expected)

    @priority.low
    def test_cannot_add_user_with_non_email_username(self, context, test_org):
        step("Try to add user with invalid username to an organization")
        username = "non-valid-username"
        org_users = User.get_list_in_organization(org_guid=test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                     User.create_by_adding_to_organization, context=context, org_guid=test_org.guid,
                                     username=username, role=User.ORG_ROLE["user"])
        step("Check that no new user was added to the organization")
        users = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(users) == sorted(org_users)

    @priority.low
    def test_cannot_add_new_user_to_non_existing_org(self, context):
        org_guid = "this-org-guid-is-not-correct"
        step("Check that an error is raised when trying to add user using incorrect org guid")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_GUID_CODE_IS_INVALID_EXCEPTION,
                                     User.create_by_adding_to_organization, context=context, org_guid=org_guid,
                                     role=User.ORG_ROLE["user"])

    @priority.medium
    @pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
    def test_non_admin_cannot_add_new_user_to_org(self, context, test_org_user_client, test_org):
        step("Try to add user to an organization using non-admin user")
        org_users = User.get_list_in_organization(org_guid=test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     User.create_by_adding_to_organization, context=context, org_guid=test_org.guid,
                                     role=User.ORG_ROLE["user"], inviting_client=test_org_user_client)
        step("Check that no new user was added to the organization")
        users = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(users) == sorted(org_users)

    @priority.low
    def test_cannot_add_new_user_with_incorrect_role(self, context, test_org):
        step("Check that error is raised when trying to add user using incorrect roles")
        role = "i-don't-exist"
        org_users = User.get_list_in_organization(org_guid=test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     User.create_by_adding_to_organization, context=context,
                                     org_guid=test_org.guid, role=role)
        step("Check that no new user was added to the organization")
        users = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(users) == sorted(org_users)

    @priority.medium
    def test_org_admin_adds_new_user(self, context, test_org, test_org_admin_client):
        step("Org admin adds a new user to an organization")
        expected_role = User.ORG_ROLE["user"]
        user = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid, role=expected_role,
                                                     inviting_client=test_org_admin_client)
        step("Check that the user was added correctly")
        assert_user_in_org_and_role(user, test_org.guid, expected_role)
