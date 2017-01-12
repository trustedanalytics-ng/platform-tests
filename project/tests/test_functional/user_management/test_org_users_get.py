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
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestGetOrganizationUsers:

    @pytest.fixture(scope="class")
    def test_org_user_clients(self, test_org_admin_client, test_org_user_client):
        """
        <b>Description:</b>
        Checks if user HTTP clients are correctly created.

        <b>Input data:</b>
        1. Email address.
        2. User password.

        <b>Expected results:</b>
        Test passes when user HTTP clients are correctly created.

        <b>Steps:</b>
        1. Create admin and non-admin user clients.
        """
        return {
            "test_org_admin_client": test_org_admin_client,
            "test_org_user_client": test_org_user_client
        }
    
    @priority.high
    def test_org_admin_can_get_org_users(self, test_org, test_org_admin_client):
        """
        <b>Description:</b>
        Checks if organization admin can retrieve organization user list.

        <b>Input data:</b>
        1. Email address.
        2. User password.

        <b>Expected results:</b>
        Test passes when organization admin can retrieve organization user list.

        <b>Steps:</b>
        1. Check that admin can get a list of users in org.
        """
        step("Check that admin can get a list of users in org")
        expected_users = User.get_list_in_organization(org_guid=test_org.guid, client=test_org_admin_client)
        user_list = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(user_list) == sorted(expected_users)

    @priority.high
    def test_platform_admin_can_get_org_users(self, admin_user, test_org, admin_client, remove_admin_from_test_org):
        """
        <b>Description:</b>
        Checks if platform admin can get user's list.

        <b>Input data:</b>
        1. No input data.

        <b>Expected results:</b>
        Test passes when platform admin can retrieve organization user list.

        <b>Steps:</b>
        1. Check that platform admin can get a list of users in any org.
        """
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        step("Check that platform admin can get a list of users in any org")
        expected_users = User.get_list_in_organization(org_guid=test_org.guid, client=admin_client)
        user_list = User.get_list_in_organization(org_guid=test_org.guid)
        assert sorted(user_list) == sorted(expected_users)

    @priority.low
    def test_org_user_cannot_get_org_users(self, test_org_user_client, test_org):
        """
        <b>Description:</b>
        Checks if non-admin cannot get user's list.

        <b>Input data:</b>
        1. Email address.
        2. User password.

        <b>Expected results:</b>
        Test passes when non-admin cannot get user's list.

        <b>Steps:</b>
        1. Check that user cannot get list of users in org.
        """
        step("Check that user cannot get list of users in org")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     User.get_list_in_organization, org_guid=test_org.guid,
                                     client=test_org_user_client)
