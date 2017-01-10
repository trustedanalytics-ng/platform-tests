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

from modules import gmail_api
from modules.constants import TapComponent as TAP, UserManagementHttpStatus, \
    TapMessage
from modules.markers import priority
from modules.tap_logger import log_fixture, step
from modules.tap_object_model import CliInvitation, User, CliUser
from modules.tap_object_model.flows.onboarding import onboard
from tests.fixtures.assertions import assert_in_with_retry, \
    assert_not_in_with_retry, assert_raises_command_execution_exception

logged_components = (TAP.user_management,)


class CliUserTestFixtures(object):

    @pytest.fixture(scope="function")
    def user(self, context, test_org, cli_login):
        new_user = onboard(context=context, org_guid=test_org.guid,
                           check_email=False)
        assert_in_with_retry(new_user, User.get_all_users,
                             org_guid=test_org.guid)
        return new_user

    @pytest.fixture(scope="function")
    def invitation(self, class_context, tap_cli):
        log_fixture("Send invitation")
        invitation = CliInvitation.send(class_context, tap_cli=tap_cli)
        assert_in_with_retry(invitation, CliInvitation.get_list, tap_cli)
        return invitation

    @pytest.fixture(scope="function")
    def regular_user(self, user, tap_cli):
        current_passwd = user.password
        username = user.username.replace('+', '%2B')
        step("New user logs in...")
        tap_cli.login(tap_auth=[username, current_passwd])
        logged_user = user
        return logged_user

    @pytest.fixture(scope="function")
    def current_username(self, regular_user):
        return regular_user.username.replace('+', '%2B')

    @pytest.fixture(scope="function")
    def current_password(self, regular_user):
        return regular_user.password


class TestCliUserOperations(CliUserTestFixtures):

    @priority.high
    @pytest.mark.components(TAP.cli, TAP.user_management)
    def test_add_user(self, test_org, user):
        """
        <b>Description:</b>
        Add user.

        <b>Input data:</b>
        1. User

        <b>Expected results:</b>
        User is successfully added and visible in users list

        <b>Steps:</b>
        1. Delete user.
        2. Check that user is present on users list.
        """
        assert_in_with_retry(user, User.get_all_users,
                             org_guid=test_org.guid)

    @priority.high
    @pytest.mark.components(TAP.cli, TAP.user_management)
    @pytest.mark.bugs("DPNG-13587 500 is returned when trying to delete user")
    def test_delete_user(self, tap_cli, test_org, user):
        """
        <b>Description:</b>
        Delete user.

        <b>Input data:</b>
        1. User

        <b>Expected results:</b>
        User is successfully deleted and no longer visible in users list

        <b>Steps:</b>
        1. Delete user.
        2. Check that user is no longer present in users list.
        """
        step("Deleting user...")
        tap_cli.delete_user(user.username)
        step("Ensuring {} has been removed from user list"
             .format(user.username))
        assert_not_in_with_retry(user, User.get_all_users,
                                 org_guid=test_org.guid)


class TestCliInvitation(CliUserTestFixtures):

    @priority.high
    @pytest.mark.components(TAP.cli)
    def test_register_user_and_check_on_list(self, context, tap_cli,
                                             test_org, invitation):
        """
        <b>Description:</b>
        Invite and register new user.

        <b>Input data:</b>
        -

        <b>Expected results:</b>
        New user is successfully registered and visible in users list.

        <b>Steps:</b>
        1. Send invitation.
        2. Register new user.
        3. Check that added user is in users list.
        """
        step("User accepts invitation and registers")
        user = CliUser.register(context, tap_cli=tap_cli,
                                username=invitation.name,
                                org_guid=test_org.guid)
        step("Check that user is on the list of users")
        users = CliUser.get_list(tap_cli=tap_cli)
        assert user in users

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_sent_invitation_is_on_pending_list(self, tap_cli, invitation):
        """
        <b>Description:</b>
        Check that invitation is shown in invitations list.

        <b>Input data:</b>
        1. Invitation

        <b>Expected results:</b>
        Invitation is shown in invitations list.

        <b>Steps:</b>
        1. Retrieve active invitations.
        2. Check that invitation is present in retrieved invitations list.
        """
        step("Check if invitation has been added to pending list")
        pending_invitations = CliInvitation.get_list(tap_cli)
        invitation = next((i for i in pending_invitations
                           if i == invitation), None)
        assert invitation is not None, \
            "Sent invitation not found on pending invitations list"

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_resend_invitation(self, tap_cli, invitation):
        """
        <b>Description:</b>
        Resend invitation.

        <b>Input data:</b>
        1. Invitation.

        <b>Expected results:</b>
        Invitation is successfully resend.

        <b>Steps:</b>
        1. Resend invitation.
        2. Check that invitation was resend.
        """
        step("Resending invitation...")
        tap_cli.reinvite(username=invitation.username)
        step("Ensuring invitation appeared in email inbox.")
        messages = gmail_api.wait_for_messages_to(recipient=invitation.username,
                                                  messages_number=2)
        assert len(messages) == 2

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_delete_invitation_and_resend(self, tap_cli, invitation):
        """
        <b>Description:</b>
        Delete pending invitation and resend.

        <b>Input data:</b>
        1. Invitation.

        <b>Expected results:</b>
        Invitation is successfully deleted
        and re-invitation returns error message.

        <b>Steps:</b>
        1. Delete invitation.
        2. Re-invite user.
        3. Check exception message.
        """
        step("Deleting invitation...")
        invitation.delete()
        expected_code = 1
        expected_message_scheme = \
            UserManagementHttpStatus.MSG_NO_PENDING_INVITATION_FOR
        expected_message = expected_message_scheme.format(invitation.username)
        step("Ensuring legitimate response has been returned")
        assert_raises_command_execution_exception(expected_code,
                                                  expected_message,
                                                  tap_cli.reinvite,
                                                  username=invitation.username)

    @priority.medium
    @pytest.mark.components(TAP.cli)
    @pytest.mark.bugs("DPNG-13587 - 500 is returned when trying to delete user.")
    def test_delete_invitation(self, tap_cli, invitation):
        """
        <b>Description:</b>
        Delete invitation.

        <b>Input data:</b>
        1. Invitation

        <b>Expected results:</b>
        Invitation is successfully deleted and no longer
        visible in active invitations list

        <b>Steps:</b>
        1. Delete invitation.
        2. Check that invitation is no longer present
           in invitations list.
        """
        step("Deleting invitation...")
        invitation.delete()
        step("Ensuring invitation has been removed")
        assert_not_in_with_retry(invitation,
                                 CliInvitation.get_list,
                                 tap_cli)


class TestChangePassword(CliUserTestFixtures):

    @priority.medium
    @pytest.mark.components(TAP.cli, TAP.user_management)
    @pytest.mark.bugs("DPNG-14955 Update tap api client expected http status")
    def test_user_change_passwd_to_valid(self, tap_cli,
                                         current_username,
                                         current_password):
        """
        <b>Description:</b>
        Changes password to valid one

        <b>Input data:</b>
        1. New password

        <b>Expected results:</b>
        Password is successfully changed

        <b>Steps:</b>
        1. Change password.
        2. Login again with new password.
        """
        new_passwd = 'NewSecurePassword'
        step("Changing password...")
        tap_cli.change_password(current=current_password, new=new_passwd)
        step("New user logs in with changed password...")
        result = tap_cli.login(tap_auth=[current_username, new_passwd])
        assert TapMessage.AUTHENTICATION_SUCCEEDED in result

    @priority.medium
    @pytest.mark.components(TAP.cli, TAP.user_management)
    @pytest.mark.bugs("DPNG-14955 Update tap api client expected http status")
    def test_user_login_with_old_passwd(self, tap_cli,
                                        current_username,
                                        current_password):
        """
        <b>Description:</b>
        Changes password and login with old password.

        <b>Input data:</b>
        1. New password

        <b>Expected results:</b>
        Authentication failed.

        <b>Steps:</b>
        1. Change password.
        2. Logout.
        3. Login again with old password.
        """
        new_passwd = 'NewSecurePassword'
        step("Changing password...")
        tap_cli.change_password(current=current_password, new=new_passwd)
        old_passwd = current_password
        step("New user logs in with old password...")
        assert_raises_command_execution_exception(1,
                                                  TapMessage.AUTHENTICATION_FAILED,
                                                  tap_cli.login,
                                                  tap_auth=[current_username,
                                                            old_passwd])

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_cannot_change_passwd_with_invalid_current(self, tap_cli):
        """
        <b>Description:</b>
        Trying to change password passing invalid password.

        <b>Input data:</b>
        1. Invalid password

        <b>Expected results:</b>
        Changing user password failed.

        <b>Steps:</b>
        1. Login.
        2. Try to change password with invalid one.
        """
        invalid_passwd = 'InvalidPassword'
        new_passwd = 'NewSecurePassword'
        step("Changing password...")
        assert_raises_command_execution_exception(1,
                                                  TapMessage.CHANGING_PASSWORD_FAILED,
                                                  tap_cli.change_password,
                                                  current=invalid_passwd,
                                                  new=new_passwd)
