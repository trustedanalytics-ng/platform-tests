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
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus, Guid
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import User
from tests.fixtures.assertions import assert_user_not_in_org, assert_user_in_org_and_role, assert_raises_http_exception

logged_components = (TAP.user_management, TAP.auth_gateway)
pytestmark = [pytest.mark.components(TAP.user_management, TAP.auth_gateway)]


class TestDeleteOrganizationUser:

    @pytest.fixture(scope="function")
    def user_to_delete(self, context, test_org):
        step("Create user to be deleted")
        return User.create_by_adding_to_organization(context=context, org_guid=test_org.guid, role=User.ORG_ROLE["user"])

    @priority.high
    def test_org_admin_can_delete_user(self, context, test_org, user_to_delete):
        """
        <b>Description:</b>
        Checks if admin user can remove other user.

        <b>Input data:</b>
        1. Email address.
        2. User password.

        <b>Expected results:</b>
        Test passes when user was successfully removed by admin user.

        <b>Steps:</b>
        1. Admin removes a user from the test org.
        2. Check that the user is not in the organization.
        """
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        step("Admin removes a user from the test org")
        user_to_delete.delete_from_organization(org_guid=test_org.guid)
        step("Check that the user is not in the organization.")
        assert_user_not_in_org(user_to_delete, test_org.guid)

    @priority.low
    def test_cannot_delete_org_user_twice(self, context, user_to_delete, test_org):
        """
        <b>Description:</b>
        Checks if a user cannot be removed twice.

        <b>Input data:</b>
        1. Email address.
        2. User password.

        <b>Expected results:</b>
        Test passes when attempt on removing the same user twice fails.

        <b>Steps:</b>
        1. Admin removes a user from the test org.
        2. Check that trying to delete test user from organization for the second time causes an error
        """
        step("Admin removes a user from the test org")
        user_to_delete.delete_from_organization(org_guid=test_org.guid)
        step("Check that trying to delete test user from organization for the second time causes an error")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_USER_NOT_EXIST,
                                     user_to_delete.delete_from_organization, org_guid=test_org.guid)

    @priority.low
    def test_admin_cannot_delete_non_existing_org_user(self, context, test_org):
        """
        <b>Description:</b>
        Checks if admin user cannot remove not existing user.

        <b>Input data:</b>
        1. No input data.

        <b>Expected results:</b>
        Test passes when attempt on removing not existing user fails.

        <b>Steps:</b>
        1. Check that an attempt to delete user which is not in org causes an error.
        """
        step("Check that an attempt to delete user which is not in org causes an error")
        non_existing_user = User(guid=Guid.NON_EXISTING_GUID, username='non-existing-user')
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_USER_NOT_EXIST,
                                     non_existing_user.delete_from_organization, org_guid=test_org.guid)

    @priority.low
    def test_non_admin_cannot_delete_user(self, context, test_org, test_org_user_client, user_to_delete):
        """
        <b>Description:</b>
        Checks if non-admin user cannot delete other user.

        <b>Input data:</b>
        1. Email address.
        2. User password.

        <b>Expected results:</b>
        Test passes when attempt on deleting other user fails and the user is still on the user's list.

        <b>Steps:</b>
        1. Check that non-admin cannot delete user from org.
        2. Check that the user was not deleted.
        """
        step("Check that non-admin cannot delete user from org")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     user_to_delete.delete_from_organization, org_guid=test_org.guid,
                                     client=test_org_user_client)
        step("Check that the user was not deleted")
        assert_user_in_org_and_role(user_to_delete, test_org.guid, user_to_delete.org_role[test_org.guid])
