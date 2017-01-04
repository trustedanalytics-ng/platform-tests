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

import re
import time

import pytest

import config
from modules import gmail_api
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus, Guid
from modules.http_calls.platform import user_management
from modules.tap_logger import step
from modules.markers import priority
from modules.tap_object_model import Invitation, User
from modules.tap_object_model.flows import onboarding
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception, assert_user_in_org_and_role

logged_components = (TAP.user_management, TAP.auth_gateway)
pytestmark = [pytest.mark.components(TAP.user_management, TAP.auth_gateway)]


class TestOnboarding:

    EXPECTED_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
    CLIENT_ID = "intel.data.tests@gmail.com"
    SENDER_PATTERN = "TrustedAnalytics <support@{}>"

    def _assert_message_correct(self, message_subject, message_content, message_sender):
        step("Check that the e-mail invitation message is correct")
        code = gmail_api.extract_code_from_message(message_content)

        expected_link_pattern = '"https?://console.{}/new-account\?code={}"'.format(config.tap_domain, code)
        message_link = gmail_api.get_link_from_message(message_content)
        correct_link = (re.match(expected_link_pattern, message_link),
                        "Link to create account: {}, expected pattern: {}".format(message_link, expected_link_pattern))

        expected_inviting_user = config.admin_username
        correct_inviting_user = (expected_inviting_user in message_content,
                                 "Inviting user {} was not found in message content.".format(expected_inviting_user))

        correct_subject = (self.EXPECTED_EMAIL_SUBJECT in message_subject,
                           "Message subject {}. Expected: {}".format(message_subject, self.EXPECTED_EMAIL_SUBJECT))

        expected_sender = self.SENDER_PATTERN.format(config.tap_domain)
        correct_sender = (expected_sender in message_sender,
                          "Message sender {}. Expected: {}".format(message_sender, expected_sender))

        error_message = [error_msg for condition, error_msg in
                         [correct_link, correct_inviting_user, correct_subject, correct_sender] if not condition]
        assert all((correct_link[0], correct_inviting_user[0], correct_subject[0])), error_message

    def _assert_user_received_messages(self, username, number_of_messages):
        step("Check that the new user received {} e-mail message(s)".format(number_of_messages))
        if number_of_messages == 0:
            time.sleep(60)  # waiting 60 sec to ensure that we will notice all messages that are about to came
            assert gmail_api.is_there_any_messages_to(username) is False, \
                "There are some messages for {} but none was expected.".format(username)

        else:
            messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=number_of_messages)
            assert len(messages) == number_of_messages, "There are {} messages for {}. Expected: {}" \
                .format(len(messages), username, number_of_messages)
            for message in messages:
                self._assert_message_correct(message["subject"], message["content"], message["sender"])

    @priority.high
    def test_simple_onboarding(self, context):
        step("Send an invite to a new user")
        invitation = Invitation.api_send(context)
        messages = gmail_api.wait_for_messages_to(recipient=invitation.username, messages_number=1)
        assert len(messages) == 1, "There are {} messages for the user. Expected: 1".format(len(messages))
        message = messages[0]
        self._assert_message_correct(message["subject"], message["content"], message["sender"])
        step("Register the new user")
        user = onboarding.register(context=context, code=invitation.code, username=invitation.username)
        step("Check that the user and their organization exist")
        assert_user_in_org_and_role(user, Guid.CORE_ORG_GUID, User.ORG_ROLE["user"])

    @priority.medium
    def test_cannot_invite_existing_user(self, context, test_org_user):
        step("Check that sending invitation to the same user causes an error.")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT,
                                     HttpStatus.MSG_USER_ALREADY_EXISTS.format(test_org_user.username),
                                     Invitation.api_send, context,
                                     username=test_org_user.username)

    @priority.high
    def test_non_admin_user_cannot_invite_another_user(self, context, test_org):
        step("Create a test user")
        user = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid,
                                                     role=User.ORG_ROLE["user"])
        non_admin_user_client = user.login()
        step("Check an error is returned when non-admin tries to onboard another user")
        username = generate_test_object_name(email=True)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_ACCESS_IS_DENIED,
                                     Invitation.api_send, context, username=username,
                                     inviting_client=non_admin_user_client)
        self._assert_user_received_messages(username, 0)

    @priority.medium
    def test_cannot_create_an_account_with_invalid_code(self, context):
        step("An error is returned when user registers with invalid code")
        username = generate_test_object_name(email=True)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                     onboarding.register, context=context, code="FFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
                                     username=username)

    @priority.medium
    @pytest.mark.bugs("DPNG-13519 500 is returned on using the same activation code twice")
    def test_cannot_use_the_same_activation_code_twice(self, context):
        step("Invite a user")
        invitation = Invitation.api_send(context)
        step("The new user registers")
        onboarding.register(context=context, code=invitation.code, username=invitation.username)
        step("Check that error is returned when the user tries to use code twice")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                     onboarding.register, context=context, code=invitation.code,
                                     username=invitation.username)

    @priority.low
    def test_invite_user_with_non_email_username(self, context):
        step("Check that passing invalid email results in error")
        username = "non_mail_username"
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                     Invitation.api_send, context=context, username=username)

    @priority.medium
    def test_user_cannot_register_without_password(self, context):
        step("Invite a new user")
        invitation = Invitation.api_send(context)
        step("Check that an error is returned when the user tries to register without a password")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_PASSWORD_CANNOT_BE_EMPTY,
                                     user_management.api_register_new_user, code=invitation.code,
                                     org_name=generate_test_object_name())
        step("Check that the user was not created")
        username_list = [user.username for user in User.get_all_users()]
        assert invitation.username not in username_list, "User was created"

