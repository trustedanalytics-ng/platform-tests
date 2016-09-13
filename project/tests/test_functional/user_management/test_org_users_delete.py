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
        return User.create_by_adding_to_organization(context, org_guid=test_org.guid, role=User.ORG_ROLE["user"])

    @priority.high
    @pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
    def test_org_admin_can_delete_user(self, context, test_org, user_to_delete):
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        step("Admin removes a user from the test org")
        user_to_delete.delete_from_organization(org_guid=test_org.guid)
        step("Check that the user is not in the organization.")
        assert_user_not_in_org(user_to_delete, test_org.guid)

    @priority.low
    @pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
    def test_cannot_delete_org_user_twice(self, context, user_to_delete, test_org):
        step("Admin removes a user from the test org")
        user_to_delete.delete_from_organization(org_guid=test_org.guid)
        step("Check that trying to delete test user from organization for the second time causes an error")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY,
                                     user_to_delete.delete_from_organization, org_guid=test_org.guid)

    @priority.low
    def test_admin_cannot_delete_non_existing_org_user(self, context, test_org):
        step("Check that an attempt to delete user which is not in org causes an error")
        non_existing_user = User(guid=Guid.NON_EXISTING_GUID, username='non-existing-user')
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_USER_NOT_EXIST,
                                     non_existing_user.delete_from_organization, org_guid=test_org.guid)

    @priority.low
    @pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
    def test_non_admin_cannot_delete_user(self, context, test_org, test_org_user_client, user_to_delete):
        step("Check that non-admin cannot delete user from org")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     user_to_delete.delete_from_organization, org_guid=test_org.guid,
                                     client=test_org_user_client)
        step("Check that the user was not deleted")
        assert_user_in_org_and_role(user_to_delete, test_org.guid, user_to_delete.org_role[test_org.guid])

    @pytest.mark.skip(reason="DPNG-10662 Deletion the last admin user is possible.")
    @priority.low
    def test_admin_cannot_delete_last_admin(self, context, test_org):
        step("Find all admins")
        org_users = User.api_get_list_via_organization(test_org.guid)
        admins = [user for user in org_users if user.ORG_ROLE[test_org.guid] == User.ORG_ROLE["admin"]]
        platform_admin = next(a for a in admins if a.username == config.admin_username)
        step("Check that it's not possible to remove last admin")
        for admin in admins:
            if admin != platform_admin:
                admin.delete_from_organization(org_guid=test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     platform_admin.delete_from_organization, org_guid=test_org.guid)

