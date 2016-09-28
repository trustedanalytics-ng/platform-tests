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
from modules.tap_object_model import Organization, User
from tests.fixtures.assertions import assert_user_in_org_and_role, assert_raises_http_exception, assert_user_not_in_org

loged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


@pytest.mark.skip(reason="Multiple organizations are not implemented for TAP_NG yet")
class TestAddExistingUserToOrganization:

    @pytest.fixture(scope="class")
    def add_user_test_cases(self):
        return {
            "add_admin": {"sent": User.ORG_ROLE["admin"], "expected": User.ORG_ROLE["admin"]},
            "add_user": {"sent": User.ORG_ROLE["user"], "expected": User.ORG_ROLE["user"]},
            "add_None": {"sent": None, "expected": User.ORG_ROLE["user"]}
        }

    @pytest.fixture(scope="class")
    def existing_user(self, class_context):
        other_org = Organization.create(class_context)
        return User.create_by_adding_to_organization(class_context, org_guid=other_org.guid)

    @pytest.fixture(scope="function", autouse=True)
    def remove_user_from_test_org(self, request, test_org, existing_user):
        request.addfinalizer(lambda: existing_user.delete_from_organization(org_guid=test_org.guid))

    @priority.medium
    @pytest.mark.parametrize("test_case", ("add_admin", "add_user", "add_None"))
    def test_add_existing_user_with_no_roles(self, context, test_org, test_case, add_user_test_cases, existing_user):
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        role_sent = add_user_test_cases[test_case]["sent"]
        role_expected = add_user_test_cases[test_case]["expected"]
        step("Add existing user to an organization with role {}".format(role_sent))
        existing_user.add_to_organization(org_guid=test_org.guid, role=role_sent)
        step("Check that the user was added with role {}".format(role_expected))
        assert_user_in_org_and_role(existing_user, test_org.guid, role_expected)

    @priority.low
    def test_add_user_which_is_already_in_org_with_the_same_role(self, test_org, existing_user):
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        expected_role = User.ORG_ROLE["admin"]
        step("Add a platform user to organization with roles {}.".format(expected_role))
        existing_user.add_to_organization(test_org.guid, roles=expected_role)
        step("Add the same user to the same organization with the same roles")
        existing_user.add_to_organization(test_org.guid, roles=expected_role)
        assert_user_in_org_and_role(existing_user, test_org.guid, expected_role)

    @priority.medium
    def test_non_admin_cannot_add_existing_user_to_org(self, context, test_org, test_org_user_client, existing_user):
        step("Check that the non-admin is not able to add a platform user to the org")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     existing_user.add_to_organization, org_guid=test_org.guid,
                                     roles=User.ORG_ROLE["user"], client=test_org_user_client)
        step("Check that the user is not in the organization.")
        assert_user_not_in_org(existing_user, test_org.guid)

    @priority.medium
    def test_user_cannot_add_themselves_to_org(self, test_org, existing_user):
        test_client = existing_user.login()
        step("Check that a platform user is not able to add themselves to the organization")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     existing_user.add_to_organization, org_guid=test_org.guid,
                                     role=User.ORG_ROLE["user"], client=test_client)
        step("Check that the user is not in the organization.")
        assert_user_not_in_org(existing_user, test_org.guid)

    @priority.low
    def test_cannot_add_existing_user_to_org_with_invalid_guid(self, existing_user):
        step("Check that adding user to organization using invalid org guid raises an error")
        invalid_org_guid = "this-org-guid-is-not-correct"
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                     existing_user.add_to_organization, org_guid=invalid_org_guid)

    @priority.low
    def test_cannot_add_existing_user_with_incorrect_role(self, test_org, existing_user):
        step("Check that it is not possible to add user to the organization with incorrect role.")
        invalid_role = ["incorrect-role"]
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                     existing_user.add_to_organization, org_guid=test_org.guid, role=invalid_role)
        step("Check that the user is not in the organization.")
        assert_user_not_in_org(existing_user, test_org.guid)
