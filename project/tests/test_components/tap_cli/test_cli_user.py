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

from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import log_fixture, step
from modules.tap_object_model import CliInvitation, User, CliUser
from modules.tap_object_model.flows.onboarding import onboard
from tests.fixtures.assertions import assert_in_with_retry, assert_not_in_with_retry


logged_components = (TAP.user_management,)


class TestCliInvitationsShort:
    SHORT = True

    @pytest.fixture(scope="class")
    def invitation(self, class_context, tap_cli, cli_login):
        log_fixture("Send invitation")
        invitation = CliInvitation.send(class_context, tap_cli=tap_cli)
        assert_in_with_retry(invitation, CliInvitation.get_list, tap_cli)
        return invitation

    @pytest.fixture(scope="function")
    def user(self, context):
        return onboard(context=context, check_email=False)

    @priority.high
    @pytest.mark.components(TAP.cli)
    def test_invite_user(self, context, tap_cli):
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
        step("Send invitation")
        invitation = CliInvitation.send(context, tap_cli=tap_cli)
        step("User accepts invitation and registers")
        user = CliUser.register(context, tap_cli=tap_cli, username=invitation.name)
        step("Check that user is on the list of users")
        users = CliUser.get_list(tap_cli=tap_cli)
        assert user in users

    @priority.medium
    @pytest.mark.components(TAP.cli)
    @pytest.mark.bugs("DPNG-13597 [api-tests] Sent invitation is not on pending list")
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
        pending_invitations = CliInvitation.get_list(tap_cli, short_cmd=self.SHORT)
        invitation = next((i for i in pending_invitations if i == invitation), None)
        assert invitation is not None, "Sent invitation not found on pending invitations list"

    @priority.high
    @pytest.mark.components(TAP.cli, TAP.user_management)
    @pytest.mark.bugs("DPNG-13587 500 is returned when trying to delete user")
    def test_delete_user(self, tap_cli, user):
        """
        <b>Description:</b>
        Delete user.

        <b>Input data:</b>
        1. User

        <b>Expected results:</b>
        User is successfully deleted and no longer visible in users list

        <b>Steps:</b>
        1. Check that user is present in users list.
        2. Delete user.
        3. Check that user is no longer present in users list.
        """
        assert_in_with_retry(user, User.get_all_users)
        tap_cli.delete_user(user.username, short=self.SHORT)
        assert_not_in_with_retry(user, User.get_all_users)

    @priority.medium
    @pytest.mark.components(TAP.cli)
    @pytest.mark.bugs("DPNG-13593 [api-tests] Could not delete user invitation")
    def test_delete_invitation(self, tap_cli, invitation):
        """
        <b>Description:</b>
        Delete invitation.

        <b>Input data:</b>
        1. Invitation

        <b>Expected results:</b>
        Invitation is successfully deleted and no longer visible in active invitations list

        <b>Steps:</b>
        1. Delete invitation.
        2. Check that invitation is no longer present in invitations list.
        """
        invitation.delete(short_cmd=self.SHORT)
        assert_not_in_with_retry(invitation, CliInvitation.get_list, tap_cli)


class TestCliInvitationsLong(TestCliInvitationsShort):
    SHORT = False
