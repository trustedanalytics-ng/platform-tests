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

from modules import file_utils
from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import AuthGatewayUser, AuthGatewayOrganization, User, Transfer
from tests.fixtures.assertions import assert_user_not_in_org

logged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.auth_gateway)]


@pytest.mark.usefixtures("open_tunnel")
class TestAuthGateway:

    @priority.high
    def test_add_user(self, test_org, context):
        """ Verify if user data are properly saved in HDFS while creating user and uploading data file to TAP.

            After create user test verifies that user is synchronized. Then login to platform as new user.
            Create transfer to HDFS and check that transfer is completed.

            Input data:
                user name: name for new user
                data file: file which is transferred to HDFS
                organization: organization wherein will be new user

            Expected results:
               It is possible to create new user and login to platform as new user. New user is able to create
               transfer to HDFS. User data are properly saved on HDFS.

            Steps:
                1. Create new user
                2. Check that user is created completely
                3. Login as new registered user
                4. Check that the user is able to create a transfer
                5. Ensure that transfer is completed successfully
        """
        step("Create new user")
        user = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid,
                                                     role=User.ORG_ROLE["user"])
        step("Check that user was synchronized")
        ag_user = AuthGatewayUser.get_user_state(org_guid=test_org.guid, user_id=user.guid)
        assert ag_user.is_synchronized, "User {} was not synchronized".format(user.username)
        step("Login new registered user")
        client = user.login()
        step("Check that the user is able to create a transfer")
        transfer = Transfer.api_create_by_file_upload(context, test_org.guid, file_utils.generate_csv_file(), client=client)
        transfer.ensure_finished()

    @priority.high
    def test_remove_user(self, context, test_org):
        """ Validate if user is properly removed from organization and from HDFS

            Create user, check that user is synchronized. Then remove user from organization and check that user is
            deleted from there. After remove check that user is not removed in auth-gateway.

            Input data:
                organization: organization wherein will be new user
                user name: name for new user

            Expected results:
                It is possible to create new user by adding to organization and remove by deleting from organization.
                User removed from organization is not in auth-gateway.

            Steps:
                1. Create new user
                2. Admin removes user from organization
                3. Check that the user is removed from organization
                4. Check that the user is removed in auth-gateway
        """
        step("Create new user")
        user_to_delete = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid,
                                                               role=User.ORG_ROLE["user"])
        removed_user_guid = user_to_delete.guid
        step("Admin removes the user from the test org")
        user_to_delete.delete_from_organization(org_guid=test_org.guid)
        step("Check that the user is not in the organization.")
        assert_user_not_in_org(user_to_delete, test_org.guid)

        user = next((u for u in AuthGatewayOrganization.get_org_state(org_guid=test_org.guid).users
                     if u.guid == removed_user_guid), None)
        assert user is None, "User was not removed in auth-gateway"
