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
from modules.tap_object_model import Organization, User
from modules.test_names import get_test_name


@log_components()
@components(TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
class Onboarding(TapTestCase):
    EXPECTED_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
    CLIENT_ID = "intel.data.tests@gmail.com"
    SENDER_PATTERN = "TrustedAnalytics <support@{}>"

    @classmethod
    def setUpClass(cls):
        cls.test_org = Organization.api_create()

    @classmethod
    def tearDownClass(cls):
        User.cf_api_tear_down_test_users()
        User.api_tear_down_test_invitations()
        Organization.cf_api_tear_down_test_orgs()

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
        username = User.api_invite()
        messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=1)
        self.assertEqual(len(messages), 1, "There are {} messages for {}. Expected: 1".format(len(messages), username))
        message = messages[0]
        self._assert_message_correct(message["subject"], message["content"], message["sender"])
        code = gmail_api.extract_code_from_message(message["content"])
        self.step("Register the new user")
        user, organization = User.api_register_after_onboarding(code, username)
        self.step("Check that the user and their organization exist")
        organizations = Organization.api_get_list()
        self.assertIn(organization, organizations, "New organization was not found")
        self.assert_user_in_org_and_roles(user, organization.guid, User.ORG_ROLES["manager"])

    @priority.medium
    def test_cannot_invite_existing_user(self):
        self.step("Invite a test user. The new user registers.")
        user, organization = User.api_onboard()
        self.step("Check that sending invitation to the same user causes an error.")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT,
                                            HttpStatus.MSG_USER_ALREADY_EXISTS.format(user.username),
                                            User.api_invite, user.username)

    @priority.high
    def test_non_admin_user_cannot_invite_another_user(self):
        self.step("Create a test user")
        non_admin_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid)
        non_admin_user_client = non_admin_user.login()
        self.step("Check an error is returned when non-admin tries to onboard another user")
        username = get_test_name(email=True)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_ACCESS_DENIED,
                                            User.api_invite, username, inviting_client=non_admin_user_client)
        self._assert_user_received_messages(username, 0)

    @priority.medium
    def test_cannot_create_an_account_with_invalid_code(self):
        self.step("An error is returned when user registers with invalid code")
        username = get_test_name(email=True)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                            User.api_register_after_onboarding, "xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                                            username)

    @priority.medium
    def test_cannot_use_the_same_activation_code_twice(self):
        self.step("Invite a user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("The new user registers")
        User.api_register_after_onboarding(code, username)
        self.step("Check that error is returned when the user tries to use code twice")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                            User.api_register_after_onboarding, code, username)

    @priority.low
    def test_invite_user_with_non_email_username(self):
        self.step("Check that passing invalid email results in error")
        username = "non_mail_username"
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_invite, username)

    @priority.medium
    def test_user_cannot_register_without_password(self):
        self.step("Invite a new user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that an error is returned when the user tries to register without a password")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_PASSWORD_CANNOT_BE_EMPTY,
                                            api.api_register_new_user, code=code, org_name=get_test_name())
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotIn(username, username_list, "User was created")

    @priority.medium
    def test_user_cannot_register_already_existing_organization(self):
        self.step("Invite a new user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that an error is returned when the user registers with an already-existing org name")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT,
                                            HttpStatus.MSG_ORGANIZATION_ALREADY_EXISTS.format(self.test_org.name),
                                            User.api_register_after_onboarding, code, username,
                                            org_name=self.test_org.name)
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotIn(username, username_list, "User was created")

    @priority.low
    def test_user_cannot_register_with_no_organization_name(self):
        self.step("Invite a new user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that an error is returned when user registers without passing an org name")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST,
                                            HttpStatus.MSG_ORGANIZATION_CANNOT_CONTAIN_ONLY_WHITESPACES,
                                            api.api_register_new_user, code=code, password="testPassw0rd")
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotIn(username, username_list, "User was created")


@log_components()
@components(TAP.user_management)
class PendingInvitations(TapTestCase):

    @priority.high
    def test_add_new_pending_invitation(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.step("Check that the user is in the pending invitation list")
        self.assertInWithRetry(username, User.api_get_pending_invitations)

    @priority.medium
    def test_accepting_invitation_deletes_it_from_pending_list(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.step("Get registration code from received message")
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Register user with the received code")
        User.api_register_after_onboarding(code, username)
        self.step("Check that invitation is no longer present in pending invitation list")
        self.assertNotInWithRetry(username, User.api_get_pending_invitations)

    @priority.medium
    def test_add_new_pending_invitation_twice_for_the_same_user(self):
        self.step("Send invitation two times for a single user")
        username = User.api_invite()
        User.api_invite(username=username)
        invitation_list = User.api_get_pending_invitations()
        self.step("Check that there is only one invitation for the user")
        self.assertEqual(invitation_list.count(username), 1, "More than one invitation for user {}".format(username))

    @priority.medium
    def test_resend_pending_invitation(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.step("Check that the user received the message")
        messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=1)
        self.assertEqual(len(messages), 1)
        self.step("Resend invitation")
        User.api_resend_user_invitation(username)
        self.step("Check that the user received the new message")
        messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=2)
        self.assertEqual(len(messages), 2)
        code = gmail_api.extract_code_from_message(messages[1]["content"])
        self.step("Register user with the received code")
        user, organization = User.api_register_after_onboarding(code, username)
        self.assert_user_in_org_and_roles(user, organization.guid, User.ORG_ROLES["manager"])

    @priority.low
    def test_cannot_resend_not_existing_pending_invitation(self):
        username = "not_existing_user"
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND,
                                            HttpStatus.MSG_NO_PENDING_INVITATION_FOR.format(username),
                                            User.api_resend_user_invitation, username)

    @priority.low
    def test_cannot_resend_invitation_providing_empty_name(self):
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_METHOD_NOT_ALLOWED, HttpStatus.MSG_METHOD_NOT_SUPPORTED.format("POST"),
                                            User.api_resend_user_invitation, "")

    @priority.medium
    def test_delete_pending_invitation(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.assertInWithRetry(username, User.api_get_pending_invitations)
        self.step("Delete pending user invitation")
        User.api_delete_user_invitation(username)
        self.assertNotInWithRetry(username, User.api_get_pending_invitations)
        self.step("Get registration code from received message")
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that the user cannot register after deletion of pending invitation")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                            User.api_register_after_onboarding, code, username)

    @priority.low
    def test_cannot_delete_not_existing_pending_invitation(self):
        self.step("Try to delete not existing invitation")
        username = "not_existing_user"
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND,
                                            HttpStatus.MSG_NO_PENDING_INVITATION_FOR.format(username),
                                            User.api_delete_user_invitation, username)

    @priority.low
    def test_cannot_delete_pending_invitation_providing_empty_name(self):
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_METHOD_NOT_ALLOWED, HttpStatus.MSG_METHOD_NOT_SUPPORTED.format("DELETE"),
                                            User.api_delete_user_invitation, "")

    @priority.medium
    def test_cannot_get_pending_invitations_as_non_admin_user(self):
        self.step("Create new org and user")
        test_org = Organization.api_create()
        test_user = User.api_create_by_adding_to_organization(test_org.guid)
        test_user_client = test_user.login()
        self.step("As non admin user try to get pending invitations list")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_ACCESS_DENIED,
                                            User.api_get_pending_invitations, test_user_client)
