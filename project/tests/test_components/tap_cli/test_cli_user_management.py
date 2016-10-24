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


logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service, TAP.cli)]


@pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
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

    @pytest.mark.bugs("DPNG-11762 [TAP_NG] 504 Gateway Time-out when adding new user")
    @priority.high
    def test_invite_user(self, context, tap_cli):
        step("Send invitation")
        invitation = CliInvitation.send(context, tap_cli=tap_cli)
        step("User accepts invitation and registers")
        user = CliUser.register(context, tap_cli=tap_cli, username=invitation.name)
        step("Check that user is on the list of users")
        users = CliUser.get_list(tap_cli=tap_cli)
        assert user in users

    @priority.medium
    def test_sent_invitation_is_on_pending_list(self, tap_cli, invitation):
        pending_invitations = CliInvitation.get_list(tap_cli, short_cmd=self.SHORT)
        invitation = next((i for i in pending_invitations if i == invitation), None)
        assert invitation is not None, "Sent invitation not found on pending invitations list"

    @pytest.mark.bugs("DPNG-11762 [TAP_NG] 504 Gateway Time-out when adding new user")
    @priority.high
    def test_delete_user(self, tap_cli, user):
        assert_in_with_retry(user, User.get_all_users)
        tap_cli.delete_user(user.username, short=self.SHORT)
        assert_not_in_with_retry(user, User.get_all_users)

    @priority.medium
    def test_delete_invitation(self, tap_cli, invitation):
        invitation.delete(short_cmd=self.SHORT)
        assert_not_in_with_retry(invitation, CliInvitation.get_list, tap_cli)


class TestCliInvitationsLong(TestCliInvitationsShort):
    SHORT = False
