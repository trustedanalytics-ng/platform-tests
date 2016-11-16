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
from tests.fixtures.assertions import assert_raises_http_exception, assert_user_in_org_and_role


logged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestGetOrganizationUsers:

    @pytest.fixture(scope="class")
    def test_org_user_clients(self, test_org_admin_client, test_org_user_client):
        return {
            "test_org_admin_client": test_org_admin_client,
            "test_org_user_client": test_org_user_client
        }

    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    @pytest.mark.parametrize("client_key", ("test_org_admin_client", "test_org_user_client"))
    @priority.low
    def test_cannot_get_users_in_another_org(self, context, test_org_user_clients, client_key):
        step("Create new organization")
        org = Organization.create(context)
        step("Check that a user or org admin not in an org cannot get list of users in the org")
        client = test_org_user_clients[client_key]
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     User.get_list_in_organization, org_guid=org.guid, client=client)

    @priority.low
    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    def test_org_admin_cannot_update_user_in_another_org(self, context, another_org, another_org_user,
                                                         test_org_admin_client):
        step("Check that user not in org cannot update another user")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                     another_org_user.update_org_role, another_org.guid,
                                     new_role=User.ORG_ROLE["admin"], client=test_org_admin_client)
        assert_user_in_org_and_role(another_org_user, another_org.guid, User.ORG_ROLE["user"])

    @priority.low
    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    def test_cannot_update_user_which_is_not_in_org(self, test_org, another_org, another_org_user):
        step("Check that user not in org cannot be updated")
        # TODO change test case to use test_org_admin_client instead of default client - when DPNG-10987 is done
        test_org_users_before = User.get_list_in_organization(org_guid=test_org.guid)
        another_org_users_before = User.get_list_in_organization(org_guid=another_org.guid)
        expected_message = HttpStatus.MSG_USER_NOT_EXIST_IN_ORGANIZATION.format(another_org_user.guid, test_org.guid)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, expected_message,
                                     another_org_user.update_org_role, org_guid=test_org.guid,
                                     new_role=User.ORG_ROLE["admin"])
        step("Check that users in either organization did not change")
        test_org_users_after = User.get_list_in_organization(org_guid=test_org.guid)
        another_org_users_after = User.get_list_in_organization(org_guid=another_org.guid)
        assert sorted(another_org_users_after) == sorted(another_org_users_before)
        assert sorted(test_org_users_after) == sorted(test_org_users_before)
