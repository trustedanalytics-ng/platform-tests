#
# Copyright (c) 2015-2016 Intel Corporation
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

from modules import gmail_api
from configuration import config
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.http_calls import platform as api
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, priority
from modules.tap_object_model import Invitation, Organization, User
from modules.tap_object_model.flows import onboarding
from modules.test_names import get_test_name
from tests.fixtures import teardown_fixtures


@log_components()
@components(TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
class Onboarding(TapTestCase):
    EXPECTED_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
    CLIENT_ID = "intel.data.tests@gmail.com"
    SENDER_PATTERN = "TrustedAnalytics <support@{}>"

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.test_org = Organization.api_create()

    def _assert_message_correct(self, message_subject, message_content, message_sender):
        self.step("Check that the e-mail invitation message is correct")
        code = gmail_api.extract_code_from_message(message_content)

        expected_link_pattern = '"https?://console.{}/new-account\?code={}"'.format(config.CONFIG["domain"], code)
        message_link = gmail_api.get_link_from_message(message_content)
        correct_link = (re.match(expected_link_pattern, message_link),
                        "Link to create account: {}, expected pattern: {}".format(message_link, expected_link_pattern))

        expected_inviting_user = config.CONFIG["admin_username"]
        correct_inviting_user = (expected_inviting_user in message_content,
                                 "Inviting user {} was not found in message content.".format(expected_inviting_user))

        correct_subject = (self.EXPECTED_EMAIL_SUBJECT in message_subject,
                           "Message subject {}. Expected: {}".format(message_subject, self.EXPECTED_EMAIL_SUBJECT))

        expected_sender = self.SENDER_PATTERN.format(config.CONFIG["domain"])
        correct_sender = (expected_sender in message_sender,
                          "Message sender {}. Expected: {}".format(message_sender, expected_sender))

        error_message = [error_msg for condition, error_msg in
                         [correct_link, correct_inviting_user, correct_subject, correct_sender] if not condition]
        self.assertTrue(all((correct_link[0], correct_inviting_user[0], correct_subject[0])), error_message)

    def _assert_user_received_messages(self, username, number_of_messages):
        self.step("Check that the new user received {} e-mail message(s)".format(number_of_messages))
        if number_of_messages == 0:
            time.sleep(60)  # waiting 60 sek to ensure that we will notice all messages that are about to came
            self.assertFalse(gmail_api.is_there_any_messages_to(username),
                             "There are some messages for {} but none was expected.".format(username))

        else:
            messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=number_of_messages)
            self.assertEqual(len(messages), number_of_messages, "There are {} messages for {}. Expected: {}"
                             .format(len(messages), username, number_of_messages))
            for message in messages:
                self._assert_message_correct(message["subject"], message["content"], message["sender"])

    @priority.high
    def test_simple_onboarding(self):
        self.step("Send an invite to a new user")
        invitation = Invitation.api_send()
        messages = gmail_api.wait_for_messages_to(recipient=invitation.username, messages_number=1)
        self.assertEqual(len(messages), 1, "There are {} messages for the user. Expected: 1".format(len(messages)))
        message = messages[0]
        self._assert_message_correct(message["subject"], message["content"], message["sender"])
        self.step("Register the new user")
        user, organization = onboarding.register(code=invitation.code, username=invitation.username)
        self.step("Check that the user and their organization exist")
        organizations = Organization.api_get_list()
        self.assertIn(organization, organizations, "New organization was not found")
        self.assert_user_in_org_and_roles(user, organization.guid, User.ORG_ROLES["manager"])

    @priority.medium
    def test_cannot_invite_existing_user(self):
        self.step("Invite a test user. The new user registers.")
        user, organization = onboarding.onboard()
        self.step("Check that sending invitation to the same user causes an error.")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT,
                                            HttpStatus.MSG_USER_ALREADY_EXISTS.format(user.username),
                                            Invitation.api_send, username=user.username)

    @priority.high
    def test_non_admin_user_cannot_invite_another_user(self):
        self.step("Create a test user")
        non_admin_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid)
        non_admin_user_client = non_admin_user.login()
        self.step("Check an error is returned when non-admin tries to onboard another user")
        username = get_test_name(email=True)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_ACCESS_DENIED,
                                            Invitation.api_send, username=username,
                                            inviting_client=non_admin_user_client)
        self._assert_user_received_messages(username, 0)

    @priority.medium
    def test_cannot_create_an_account_with_invalid_code(self):
        self.step("An error is returned when user registers with invalid code")
        username = get_test_name(email=True)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                            onboarding.register, code="xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                                            username=username)

    @priority.medium
    def test_cannot_use_the_same_activation_code_twice(self):
        self.step("Invite a user")
        invitation = Invitation.api_send()
        self.step("The new user registers")
        onboarding.register(invitation.code, invitation.username)
        self.step("Check that error is returned when the user tries to use code twice")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                            onboarding.register, code=invitation.code, username=invitation.username)

    @priority.low
    def test_invite_user_with_non_email_username(self):
        self.step("Check that passing invalid email results in error")
        username = "non_mail_username"
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            Invitation.api_send, username=username)

    @priority.medium
    def test_user_cannot_register_without_password(self):
        self.step("Invite a new user")
        invitation = Invitation.api_send()
        self.step("Check that an error is returned when the user tries to register without a password")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_PASSWORD_CANNOT_BE_EMPTY,
                                            api.api_register_new_user, code=invitation.code, org_name=get_test_name())
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotIn(invitation.username, username_list, "User was created")

    @priority.medium
    def test_user_cannot_register_already_existing_organization(self):
        self.step("Invite a new user")
        invitation = Invitation.api_send()
        self.step("Check that an error is returned when the user registers with an already-existing org name")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT,
                                            HttpStatus.MSG_ORGANIZATION_ALREADY_EXISTS.format(self.test_org.name),
                                            onboarding.register, code=invitation.code, username=invitation.username,
                                            org_name=self.test_org.name)
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotIn(invitation.username, username_list, "User was created")

    @priority.low
    def test_user_cannot_register_with_no_organization_name(self):
        self.step("Invite a new user")
        invitation = Invitation.api_send()
        self.step("Check that an error is returned when user registers without passing an org name")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST,
                                            HttpStatus.MSG_ORGANIZATION_CANNOT_CONTAIN_ONLY_WHITESPACES,
                                            api.api_register_new_user, code=invitation.code,
                                            password=User.generate_password())
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotIn(invitation.username, username_list, "User was created")

