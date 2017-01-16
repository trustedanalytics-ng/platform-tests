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

import config
import pytest

from modules.constants import TapComponent as TAP, Guid
from modules.constants import UserManagementHttpStatus as HttpStatus
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import KubernetesPod
from modules.tap_object_model.flows import onboarding
from modules.tap_object_model.invitation import Invitation
from modules.tap_object_model.user import User
from tests.fixtures.assertions import assert_user_in_org_and_role
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.user_management,)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestUserManagement:
    POD_NAME_PREFIX = "user-management"

    @pytest.fixture(scope="class")
    def tap_users(self, test_org):
        return User.get_all_users(org_guid=test_org.guid)

    @pytest.fixture(scope="class")
    def all_admins(self, test_org, tap_users):
        return [user for user in tap_users if user.org_role[test_org.guid] ==
                User.ORG_ROLE["admin"]]

    @pytest.fixture(scope="class")
    def platform_admin(self, tap_users):
        return next(admin for admin in tap_users if admin.username ==
                    config.admin_username)

    @pytest.fixture(scope="class")
    def other_admins(self, all_admins, platform_admin):
        return [admin for admin in all_admins
                if admin.username != platform_admin.username]

    @pytest.fixture(scope="function")
    def restore_admin_roles(self, request, test_org, other_admins):
        def fin():
            step("Restore ADMIN role for all initially present admins")
            for initially_present_admin in other_admins:
                initially_present_admin.update_org_role(
                    org_guid=test_org.guid, new_role=User.ORG_ROLE["admin"])
        request.addfinalizer(fin)

    @pytest.mark.usefixtures("open_tunnel")
    @priority.low
    def test_use_invitation_after_pod_restart(self, context, test_org):
        """
        <b>Description:</b>
        Checks if user invitation is valid after user-management POD restart.

        <b>Input data:</b>
        1. User name.
        2. Password.

        <b>Expected results:</b>
        Test passes when user was correctly added to the platform.

        <b>Steps:</b>
        1. Invite new user.
        2. Retrieve user-management POD
        2. Restart user-management POD, verify health.
        3. Register user with the invitation.
        """

        step("Invite new user")
        invitation = Invitation.api_send(context)

        step("Retrieve user-management pod")
        pods_list = KubernetesPod.get_list()
        user_mngt_pod = next((pod for pod in pods_list if
                              pod.name.startswith(self.POD_NAME_PREFIX)), None)
        assert user_mngt_pod is not None, \
            "POD {} wasn't found on the PODs list".format(self.POD_NAME_PREFIX)

        step("Restart user-management POD, verify health")
        user_mngt_pod.restart_pod()
        user_mngt_pod.ensure_pod_in_good_health()

        step("Register user with the invitation")
        user = onboarding.register(context=context, org_guid=test_org.guid,
                                   code=invitation.code,
                                   username=invitation.username)
        assert_user_in_org_and_role(user, test_org.guid,
                                    User.ORG_ROLE["user"])

    @priority.low
    @pytest.mark.usefixtures("restore_admin_roles")
    def test_cannot_remove_admin_role_from_the_last_org_admin(
            self, test_org, platform_admin, other_admins):
        """
        <b>Description:</b>
        Checks that it is impossible to remove ADMIN role from the last admin

        <b>Input data:</b>
        1. Organization ID
        2. List of users with ADMIN role
        3. Platform Admin account name

        <b>Expected results:</b>
        Exception is thrown when trying to remove ADMIN role from the last admin

        <b>Steps:</b>
        1. Remove ADMIN role from all admins excluding Platform Admin
        2. Try to remove ADMIN role from the last admin (Platform Admin in this
           case), assert raises exception
        3. Restore ADMIN role for all initially present admins
        """

        step("Remove admin role from all admins excluding platform admin")
        for admin in other_admins:
            admin.update_org_role(org_guid=test_org.guid,
                                  new_role=User.ORG_ROLE["user"])

        step("Remove admin role from the last admin (platform admin),"
             " assert raises exception")
        assert_raises_http_exception(
            HttpStatus.CODE_FORBIDDEN,
            HttpStatus.MSG_CANNOT_PERFORM_REQ_ON_YOURSELF,
            platform_admin.update_org_role, org_guid=test_org.guid,
            new_role=User.ORG_ROLE["user"]
        )

    @priority.low
    def test_admin_cannot_delete_last_admin(self, test_org, platform_admin):
        """
        <b>Description:</b>
        Checks that it is impossible to remove the last admin account.

        This test relies on the assumption that non-admin user cannot delete
        other user accounts. It implies that the only possible way to delete
        the last admin account is to try to delete "yourself" (the account
        with which you're attempting to perform test/send request). In this test
        we try to delete the admin account that the test itself uses
        (it is not necessarily the last admin account in the TAP instance).

        The reason why we do it this way is that it would be impossible to
        restore the admin accounts if we removed them all during the test except
        the last one (we don't know the passwords of admin users up front).

        <b>Input data:</b>
        1. Organization ID
        2. Platform Admin account name

        <b>Expected results:</b>
        Exception is thrown when trying to remove the admin account which test
        uses.

        <b>Steps:</b>
        1. Check that it's not possible to remove the Platform Admin account
        """

        step("Check that it's not possible to remove platform admin")
        assert_raises_http_exception(
            HttpStatus.CODE_FORBIDDEN,
            HttpStatus.MSG_CANNOT_PERFORM_REQ_ON_YOURSELF,
            platform_admin.delete_from_organization, org_guid=test_org.guid
        )
