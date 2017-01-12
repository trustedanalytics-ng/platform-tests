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
import config

from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.http_calls.platform import user_management
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, User
from tests.fixtures.assertions import assert_user_in_org_and_role, assert_raises_http_exception

logged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestUpdateOrganizationUser:

    @pytest.fixture(scope="class")
    def update_test_cases(self, class_context, test_org):
        step("Create users to be updated")
        roles_to_update = {
            "admin_to_user": {
                "before": User.ORG_ROLE["admin"],
                "after": User.ORG_ROLE["user"],
                "expected": User.ORG_ROLE["user"]
            },
            "user_to_admin": {
                "before": User.ORG_ROLE["user"],
                "after": User.ORG_ROLE["admin"],
                "expected": User.ORG_ROLE["admin"]
            },
        }
        for key, val in roles_to_update.items():
            val["user"] = User.create_by_adding_to_organization(context=class_context, org_guid=test_org.guid,
                                                                role=val["before"])
        return roles_to_update

    @pytest.fixture(scope="function")
    def updated_user(self, context, test_org):
        step("Create test user in test org")
        return User.create_by_adding_to_organization(context=context, org_guid=test_org.guid)

    @priority.high
    @pytest.mark.parametrize("test_case_name", ("admin_to_user", "user_to_admin"))
    def test_update_org_role(self, test_org, test_case_name, update_test_cases):
        """
        <b>Description:</b>
        Checks if user role can be updated.

        <b>Input data:</b>
        1. Email address.
        2. User password.

        <b>Expected results:</b>
        Test passes when user role was correctly updated.

        <b>Steps:</b>
        1. Update user from old role to new role.
        2. Check that user's new role is correct.
        """
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        role_before = update_test_cases[test_case_name]["before"]
        role_after = update_test_cases[test_case_name]["after"]
        role_expected = update_test_cases[test_case_name]["expected"]
        updated_user = update_test_cases[test_case_name]["user"]

        step("Update user from {} to {}".format(role_before, role_after))
        updated_user.update_org_role(org_guid=test_org.guid, new_role=role_after)
        step("Check that user's new role is {}".format(role_expected))
        assert_user_in_org_and_role(updated_user, test_org.guid, role_expected)

    @priority.low
    def test_cannot_update_user_with_invalid_guid(self, test_org):
        """
        <b>Description:</b>
        Checks if user update with invalid guid fails.

        <b>Input data:</b>
        1. User guid.

        <b>Expected results:</b>
        Test passes when attempt on updating user fails and users list doesn't change.

        <b>Steps:</b>
        1. Check that updating user with invalid user guid returns an error.
        2. Check that user org list did not change.
        """
        # TODO implement non-existing guid
        step("Check that updating user with invalid user guid returns an error")
        invalid_guid = "invalid-user-guid"
        org_users = User.get_list_in_organization(org_guid=test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_GUID_CODE_IS_INVALID_EXCEPTION,
                                     user_management.api_update_org_user_role, org_guid=test_org.guid,
                                     user_guid=invalid_guid, new_role=User.ORG_ROLE["user"])
        step("Check that user org list did not change")
        users = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(users) == sorted(org_users)

    @pytest.mark.bugs("DPNG-14948 It is possible to add user to not existing org or update user providing invalid org_guid")
    @priority.low
    def test_cannot_update_org_user_with_invalid_org_guid(self, updated_user):
        """
        <b>Description:</b>
        Checks if user update with invalid organization guid fails.

        <b>Input data:</b>
        1. Organization guid.

        <b>Expected results:</b>
        Test passes when attempt on updating user with invalid organization guid fails.

        <b>Steps:</b>
        1. Check that updating user using invalid org guid returns an error.
        """
        # TODO implement non-existing guid
        invalid_guid = "invalid-org-guid"
        step("Check that updating user using invalid org guid returns an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_GUID_CODE_IS_INVALID_EXCEPTION,
                                     user_management.api_update_org_user_role, org_guid=invalid_guid,
                                     user_guid=updated_user.guid, new_role=User.ORG_ROLE["user"])

    @priority.low
    def test_cannot_update_org_user_with_incorrect_role(self, test_org, updated_user):
        """
        <b>Description:</b>
        Checks if user update with invalid role fails.

        <b>Input data:</b>
        1. Role name.

        <b>Expected results:</b>
        Test passes when attempt on updating user with invalid role fails.

        <b>Steps:</b>
        1. Check that updating user using invalid role returns an error.
        2. Check that user roles did not change.
        """
        initial_role = updated_user.org_role.get(test_org.guid)
        invalid_role = "invalid role"
        step("Check that updating user using invalid role returns an error")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     updated_user.update_org_role, org_guid=test_org.guid, new_role=invalid_role)
        step("Check that user roles did not change")
        assert_user_in_org_and_role(updated_user, test_org.guid, initial_role)

    @priority.medium
    def test_user_cannot_update_org_user(self, context, test_org, test_org_user_client, updated_user):
        """
        <b>Description:</b>
        Checks if non-admin user cannot update other user's roles.

        <b>Input data:</b>
        1. No input data.

        <b>Expected results:</b>
        Test passes when attempt on updating user role by non-admin user fails.

        <b>Steps:</b>
        1. Check that non-admin cannot update another user's roles.
        2. Check that updated user's roles did not change.
        """
        step("Check that non-admin cannot update another user's roles")
        org_users = User.get_list_in_organization(org_guid=test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     updated_user.update_org_role, org_guid=test_org.guid,
                                     new_role=User.ORG_ROLE["admin"], client=test_org_user_client)
        step("Check that updated user's roles did not change")
        users = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(users) == sorted(org_users)

    @pytest.mark.fixture(scope="class")
    def another_org(self, context):
        step("Create test organization")
        return Organization.create(context)

    @pytest.mark.fixture(scope="class")
    def another_org_user(self, context, another_org):
        step("Add users to the organization")
        User.create_by_adding_to_organization(context=context, org_guid=another_org.guid, role=User.ORG_ROLE["admin"])
        return User.create_by_adding_to_organization(context=context, org_guid=another_org.guid,
                                                     role=User.ORG_ROLE["user"])


