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
from modules.markers import incremental
from modules.tap_logger import log_fixture
from modules.tap_object_model import Invitation, User
from modules.tap_object_model.flows.onboarding import register, onboard
from modules.test_names import generate_test_object_name


@incremental
@pytest.mark.bugs("DPNG-10189 Make smtp secret configurable during deployment")
class TestCLIInvitingUser:
    @staticmethod
    @pytest.fixture(scope="class")
    def email():
        return generate_test_object_name(email=True)

    @staticmethod
    @pytest.fixture(scope="class")
    def send_invitation(tap_cli, email, cli_login):
        log_fixture("Sending invitation")
        tap_cli.invite(email)

    @pytest.mark.usefixtures("send_invitation")
    def test_sent_invitation_is_on_pending_list(self, email):
        pending_invitations = Invitation.api_get_list()
        invitation = next((i for i in pending_invitations if i.username == email), None)
        assert invitation is not None, "Sent invitation not found on pending list"

    @staticmethod
    @pytest.fixture(scope="class")
    def accept_invitation(class_context, email):
        log_fixture("Accepting invitation and registering user")
        code = gmail_api.get_invitation_code_for_user(email)
        register(class_context, code, email)

    @pytest.mark.usefixtures("accept_invitation")
    def test_1_user_registered(self, email):
        users = User.get_all_users()
        user = next((u for u in users if u.username == email), None)
        assert user is not None, "User not registered"


@pytest.mark.usefixtures("cli_login")
class TestCLIDeletingUser:
    @staticmethod
    @pytest.fixture
    def user(context):
        return onboard(context, check_email=False)

    @pytest.mark.bugs("DPNG-11762 [TAP_NG] 504 Gateway Time-out when adding new user")
    @pytest.mark.parametrize("short", (True, False))
    def test_delete_user(self, user, tap_cli, short):
        tap_cli.delete_user(user.username, short=short)
        users = User.get_all_users()
        user = next((u for u in users if u.username == user.username), None)
        assert user is None, "User is not deleted"
