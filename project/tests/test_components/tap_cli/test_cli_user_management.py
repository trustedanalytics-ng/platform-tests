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

from modules.markers import incremental
from modules.tap_logger import log_fixture
from modules.tap_object_model import CliInvitation, User
from modules.tap_object_model.cli_user import CliUser
from modules.tap_object_model.flows.onboarding import onboard
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_in_with_retry, assert_not_in_with_retry


@incremental
@pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
@pytest.mark.bugs("DPNG-11086 API SERVICE - User Management endpoints")
class TestCLIInvitingUser:
    @staticmethod
    @pytest.fixture(scope="class")
    def email():
        return generate_test_object_name(email=True)

    @staticmethod
    @pytest.fixture(scope="class")
    def invitation(class_context, tap_cli, email, cli_login):
        log_fixture("Sending invitation")
        return CliInvitation.send(class_context, tap_cli, email)

    def test_0_sent_invitation_is_on_pending_list(self, tap_cli, invitation):
        pending_invitations = CliInvitation.get_list(tap_cli)
        invitation = next((i for i in pending_invitations if i == invitation), None)
        assert invitation is not None, "Sent invitation not found on pending list"

    @staticmethod
    @pytest.fixture(scope="class")
    def user(class_context, invitation):
        log_fixture("Accepting invitation and registering user")
        return CliUser.register(class_context, invitation)

    @pytest.mark.usefixtures("accept_invitation")
    def test_1_user_registered(self, tap_cli, user):
        users = CliUser.get_list(tap_cli)
        matched_user = next((u for u in users if u == user), None)
        assert matched_user is not None, "User not registered"


@pytest.mark.usefixtures("cli_login")
@pytest.mark.bugs("DPNG-11086 API SERVICE - User Management endpoints")
class TestCLILongShortCommands:

    @staticmethod
    @pytest.fixture
    def user(context):
        return onboard(context=context, check_email=False)

    @pytest.mark.bugs("DPNG-11762 [TAP_NG] 504 Gateway Time-out when adding new user")
    @pytest.mark.parametrize("short", (True, False))
    def test_delete_user(self, tap_cli, user, short):
        assert_in_with_retry(user, User.get_all_users)
        tap_cli.delete_user(user.username, short=short)
        assert_not_in_with_retry(user, User.get_all_users)

    @staticmethod
    @pytest.fixture
    def invitation(context, tap_cli):
        return CliInvitation.send(context=context,
                                  tap_cli=tap_cli,
                                  username=generate_test_object_name(email=True))

    @pytest.mark.parametrize("short", (True, False))
    def test_invitations(self, tap_cli, invitation, short):
        assert_in_with_retry(invitation, tap_cli.invitations, short=short)

    @pytest.mark.parametrize("short", (True, False))
    def test_delete_invitations(self, tap_cli, invitation, short):
        assert_in_with_retry(invitation, CliInvitation.get_list, tap_cli)
        invitation.delete(short_cmd=short)
        assert_not_in_with_retry(invitation, CliInvitation.get_list, tap_cli)
