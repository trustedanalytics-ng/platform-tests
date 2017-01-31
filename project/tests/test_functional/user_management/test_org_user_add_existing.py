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

logged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestAddExistingUserToOrganization:

    @pytest.fixture(scope="class")
    def add_user_test_cases(self):
        return {
            "add_admin": {"sent": User.ORG_ROLE["admin"], "expected": User.ORG_ROLE["admin"]},
            "add_user": {"sent": User.ORG_ROLE["user"], "expected": User.ORG_ROLE["user"]},
            "add_None": {"sent": None, "expected": User.ORG_ROLE["user"]}
        }

    @pytest.fixture(scope="function")
    def existing_user(self, context, test_org):
        step("Create test user in test org")
        return User.create_by_adding_to_organization(context=context, org_guid=test_org.guid)

    @pytest.fixture(scope="function", autouse=True)
    def remove_user_from_test_org(self, request, test_org, existing_user):
        request.addfinalizer(lambda: existing_user.delete_from_organization(org_guid=test_org.guid))

    @priority.medium
    @pytest.mark.parametrize("test_case", ("add_admin", "add_user", "add_None"))
    def test_add_existing_user_with_valid_roles_returns_conflict(
            self, test_org, test_case, add_user_test_cases, existing_user):
        """
        <b>Description:</b>
        Checks that adding already existing user with valid roles returns conflict

        <b>Input data:</b>
        1. Test organization
        2. Test cases with different roles requests
        3. Existing user

        <b>Expected results:</b>
        Test passes when each attempt on adding existing user with valid or empty
        roles returns 409 Conflict

        <b>Steps:</b>
        1. Prepare test cases of different role change requests
        2. Check that adding existing user to an organization in every case returns 409 Conflict
        """

        role_initial = existing_user.org_role[test_org.guid]
        role_sent = add_user_test_cases[test_case]["sent"]

        step("Check that adding existing user to an organization with role {}, "
             "returns 409 Conflict".format(role_sent))
        assert_raises_http_exception(
            HttpStatus.CODE_CONFLICT,
            HttpStatus.MSG_USER_ALREADY_EXISTS.format(existing_user.username),
            existing_user.add_to_organization, org_guid=test_org.guid, role=role_sent
        )

        step("Check that the user is still in org with unchanged role {}".format(role_initial))
        assert_user_in_org_and_role(existing_user, test_org.guid, role_initial)

    @priority.low
    def test_add_existing_user_with_invalid_role_returns_bad_request(self, test_org, existing_user):
        """
        <b>Description:</b>
        Checks that adding already existing user with invalid roles returns 400 Bad Request

        <b>Input data:</b>
        1. Test organization
        2. Invalid role change request data
        3. Existing user

        <b>Expected results:</b>
        Test passes when an attempt on adding existing user with invalid role returns
        400 Bad Request

        <b>Steps:</b>
        1. Prepare invalid role change request
        2. Check that adding existing user to an organization with invalid role returns
           400 Bad Request
        """

        invalid_role = "invalid-role"

        step("Check that it is not possible to add user to the organization with incorrect role.")
        assert_raises_http_exception(
            HttpStatus.CODE_BAD_REQUEST,
            HttpStatus.MSG_BAD_REQUEST,
            existing_user.add_to_organization, org_guid=test_org.guid, role=invalid_role
        )

    @priority.medium
    def test_existing_user_add_himself_to_org_returns_forbidden(self, test_org, existing_user):
        """
        <b>Description:</b>
        Checks that when user adds himself to organization 401 Forbidden is returned

        <b>Input data:</b>
        1. Test organization
        2. Existing user

        <b>Expected results:</b>
        Test passes when an attempt on user adding himself returns 401 Forbidden

        <b>Steps:</b>
        1. Check that when user adds himself to the organization 403 Forbidden is returned
        """
        test_client = existing_user.login()

        step("Check that when user adds himself to the organization 403 Forbidden is returned")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     existing_user.add_to_organization, org_guid=test_org.guid,
                                     role=User.ORG_ROLE["user"], client=test_client)

    @priority.low
    def test_add_existing_user_to_not_existing_org_returns_not_found(self, existing_user):
        """
        <b>Description:</b>
        Checks that adding existing user to not existing organization returns 404 Not Found

        <b>Input data:</b>
        1. Test organization
        2. Existing user

        <b>Expected results:</b>
        Test passes when an attempt on adding user to not existing organizations
        returns 404 Not Found

        <b>Steps:</b>
        1. Check that adding existing user to not existing organization returns 404 Not Found
        """
        org_id = "id-of-not-existing-organization"

        step("Check that adding existing user to not existing organization returns 404 Not Found")
        assert_raises_http_exception(
            HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_ORGANIZATION_NOT_FOUND.format(org_id),
            existing_user.add_to_organization, org_guid=org_id
        )
