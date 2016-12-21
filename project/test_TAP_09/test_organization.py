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
from modules.constants import TapComponent as TAP, UserManagementHttpStatus
from modules.hive import Hive
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Organization, Space, User
from modules.tap_object_model.flows.onboarding import onboard
from modules.test_names import escape_hive_name
from tests.fixtures import assertions


logged_components = (TAP.user_management, TAP.auth_gateway)
pytestmark = [pytest.mark.components(TAP.auth_gateway, TAP.user_management)]


@pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
class TestOrganization:

    @priority.high
    def test_create_delete_organization(self, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Check that the organization is on the organization list")
        orgs = Organization.api_get_list()
        assert test_org in orgs
        step("Delete the organization")
        test_org.api_delete()
        step("Check that the organization is not on org list")
        assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)

    @priority.medium
    def test_rename_organization(self, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Update the organization, giving it new name")
        new_name = "new-{}".format(test_org.name)
        test_org.rename(new_name)
        step("Check that the organization with new name is on the organization list")
        orgs = Organization.api_get_list()
        assert test_org in orgs

    @priority.low
    def test_delete_organization_with_user(self, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Add new platform user to the organization")
        User.api_create_by_adding_to_organization(context, test_org.guid)
        step("Delete the organization")
        test_org.api_delete()
        step("Check that the organization is not on org list")
        assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)

    @priority.low
    def test_delete_organization_with_space(self, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Create a space")
        Space.api_create(org=test_org)
        step("Delete the organization")
        test_org.api_delete()
        step("Check that the organization is not on org list")
        assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)

    @priority.medium
    def test_non_admin_cannot_create_org(self, test_org_manager_client, context):
        step("Attempt to create organization with the non admin client")
        assertions.assert_raises_http_exception(UserManagementHttpStatus.CODE_FORBIDDEN,
                                                UserManagementHttpStatus.MSG_FORBIDDEN, Organization.api_create,
                                                context=context, client=test_org_manager_client)

    @priority.high
    def test_non_admin_cannot_delete_org(self, test_org_manager_client, context):
        step("Create an organization")
        test_org = Organization.api_create(context)
        step("Attempt to delete the organization with the non admin client")
        assertions.assert_raises_http_exception(UserManagementHttpStatus.CODE_FORBIDDEN,
                                                UserManagementHttpStatus.MSG_FORBIDDEN, test_org.api_delete,
                                                client=test_org_manager_client)

    @pytest.mark.bugs("DPNG-6841 Bad error message when creating org with existing name")
    @priority.medium
    def test_cannot_create_two_orgs_with_the_same_name(self, test_org, context):
        step("Attempt to create organization with the same name")
        error_message = UserManagementHttpStatus.MSG_ORGANIZATION_ALREADY_TAKEN.format(test_org.name)
        assertions.assert_raises_http_exception(UserManagementHttpStatus.CODE_BAD_REQUEST, error_message,
                                                Organization.api_create, context=context, name=test_org.name,
                                                delete_on_fail=False)

    @priority.low
    @pytest.mark.parametrize("org_name", ("a" * 100, "simple name"), ids=("long_name", "space_in_name"))
    def test_create_and_delete_org_with_special_name(self, org_name, context):
        step("Create an organization")
        test_org = Organization.api_create(context, name=org_name)
        assert org_name == test_org.name
        step("Check that the organization is on the organization list")
        orgs = Organization.api_get_list()
        assert test_org in orgs
        step("Delete the organization")
        test_org.api_delete()
        step("Check that the organization is not on org list")
        assertions.assert_not_in_with_retry(test_org, Organization.api_get_list)

    def _get_hive_databases(self, user):
        step("Connect to hive and get databases")
        hive = Hive(user)
        return hive.exec_query("show databases;")

    @priority.medium
    def test_user_can_see_org_hive_database(self, test_org, admin_user, add_admin_to_test_org):
        user_databases = self._get_hive_databases(admin_user)
        assert escape_hive_name(test_org.guid) in user_databases, "User cannot see their database"

    @priority.medium
    @pytest.mark.skipif(not config.kerberos, reason="Only on kerberos access to dbs for other orgs is blocked")
    def test_users_cannot_see_hive_databases_for_other_orgs(self, test_org, admin_user, add_admin_to_test_org, context):
        org1 = test_org
        user1 = admin_user
        step("Create second user and organization")
        user2, org2 = onboard(context, test_org.guid)
        org1_database_name = escape_hive_name(org1.guid)
        user1_databases = self._get_hive_databases(user1)
        org2_database_name = escape_hive_name(org2.guid)
        user2_databases = self._get_hive_databases(user2)

        assert org1_database_name not in user2_databases, "User can see the other user's database"
        assert org2_database_name not in user1_databases, "User can see the other user's database"
