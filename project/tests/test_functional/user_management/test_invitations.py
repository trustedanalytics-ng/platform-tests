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

from modules.constants import Guid
from modules import gmail_api
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model.invitation import Invitation
from modules.tap_object_model.user import User
from modules.tap_object_model.flows import onboarding
from tests.fixtures.assertions import assert_in_with_retry, assert_not_in_with_retry, assert_user_in_org_and_role, \
    assert_raises_http_exception

logged_components = (TAP.user_management,)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestPendingInvitations:

    @priority.high
    def test_add_new_pending_invitation(self, context):
        """
        <b>Description:</b>
        Checks if new pending invitations can be added.

        <b>Input data:</b>
        1. Email address.

        <b>Expected results:</b>
        Test passes when new pending invitation appears on pending invitations list.

        <b>Steps:</b>
        1. Invite new user.
        2. Check that the user is in the pending invitation list.
        """
        step("Invite new user")
        invitation = Invitation.api_send(context)
        step("Check that the user is in the pending invitation list")
        assert_in_with_retry(invitation, Invitation.api_get_list)

    @priority.medium
    def test_accepting_invitation_deletes_it_from_pending_list(self, context, test_org):
        """
        <b>Description:</b>
        Checks if invitation is removed from pending invitations list after invitation acceptance.

        <b>Input data:</b>
        1. Password.
        2. Email address.

        <b>Expected results:</b>
        Test passes when pending invitation is not present on pending invitations list after invitation acceptance.

        <b>Steps:</b>
        1. Invite new user.
        2. Register user with the received code.
        3. Check that invitation is no longer present in pending invitation list.
        """
        step("Invite new user")
        invitation = Invitation.api_send(context)
        step("Register user with the received code")
        onboarding.register(context=context, org_guid=test_org.guid,
                            code=invitation.code, username=invitation.username)
        step("Check that invitation is no longer present in pending invitation list")
        assert_not_in_with_retry(invitation, Invitation.api_get_list)

    @priority.medium
    def test_add_new_pending_invitation_twice_for_the_same_user(self, context):
        """
        <b>Description:</b>
        Checks if number of pending invitations is correct for a user that got 2 invitations.

        <b>Input data:</b>
        1. Email address.

        <b>Expected results:</b>
        Test passes when user to whom 2 invitations were sent has only 1 pending invitation on pending invitations
        list.

        <b>Steps:</b>
        1. Send invitation two times for a single user.
        2. Check that there is only one invitation for the user.
        """
        step("Send invitation two times for a single user")
        invitation = Invitation.api_send(context)
        Invitation.api_send(context, username=invitation.username)
        invited_users = [i.username for i in Invitation.api_get_list()]
        step("Check that there is only one invitation for the user")
        assert invited_users.count(invitation.username) == 1, "More than one invitation for the user"

    @priority.medium
    def test_resend_pending_invitation(self, context, test_org):
        """
        <b>Description:</b>
        Checks if resending emails works.

        <b>Input data:</b>
        1. Password.
        2. Email address.

        <b>Expected results:</b>
        Test passes when user obtained email with invitation and second email with invitation after it's resent.

        <b>Steps:</b>
        1. Invite new user.
        2. Check that the user received the message.
        3. Resend invitation.
        4. Check that the user received the new message.
        5. Register user with the received code.
        """
        step("Invite new user")
        invitation = Invitation.api_send(context)
        step("Check that the user received the message")
        messages = gmail_api.wait_for_messages_to(recipient=invitation.username, messages_number=1)
        assert len(messages) == 1
        step("Resend invitation")
        invitation.api_resend()
        step("Check that the user received the new message")
        messages = gmail_api.wait_for_messages_to(recipient=invitation.username, messages_number=2)
        assert len(messages) == 2
        step("Register user with the received code")
        user = onboarding.register(context=context, org_guid=test_org.guid,
                                   code=invitation.code,
                                   username=invitation.username)
        assert_user_in_org_and_role(user, test_org.guid, User.ORG_ROLE["user"])

    @priority.low
    def test_cannot_resend_not_existing_pending_invitation(self):
        """
        <b>Description:</b>
        Checks if resending emails doesn't work for not existing invitations.

        <b>Input data:</b>
        1. User name.

        <b>Expected results:</b>
        Test passes when HTTP request resending invitation returns status code 404 NOT FOUND.

        <b>Steps:</b>
        1. Resend invitation.
        """
        username = "not_existing_user"
        invitation = Invitation(username=username)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     HttpStatus.MSG_NO_PENDING_INVITATION_FOR.format(username),
                                     invitation.api_resend)

    @priority.low
    def test_cannot_resend_invitation_providing_empty_name(self):
        """
        <b>Description:</b>
        Checks if resending emails doesn't work for invitation with empty user name.

        <b>Input data:</b>
        1. User name.

        <b>Expected results:</b>
        Test passes when HTTP request resending invitation returns status code 405 NOT ALLOWED.

        <b>Steps:</b>
        1. Resend invitation.
        """
        invitation = Invitation(username="")
        assert_raises_http_exception(HttpStatus.CODE_METHOD_NOT_ALLOWED,
                                     HttpStatus.MSG_METHOD_NOT_SUPPORTED.format("POST"),
                                     invitation.api_resend)

    @priority.medium
    def test_delete_pending_invitation(self, context, test_org):
        """
        <b>Description:</b>
        Checks if user cannot use obtained invitation after it was removed from pending invitations list.

        <b>Input data:</b>
        1. Email address.

        <b>Expected results:</b>
        Test passes when registering user fails returning HTTP status code 403 FORBIDDEN.

        <b>Steps:</b>
        1. Invite new user
        2. Delete pending user invitation.
        3. Check that the user cannot register after deletion of pending invitation.
        """
        step("Invite new user")
        invitation = Invitation.api_send(context)
        assert_in_with_retry(invitation, Invitation.api_get_list)
        step("Delete pending user invitation")
        invitation.api_delete()
        assert_not_in_with_retry(invitation, Invitation.api_get_list)
        step("Check that the user cannot register after deletion of pending invitation")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                     onboarding.register, context=context,
                                     org_guid=test_org.guid,
                                     code=invitation.code,
                                     username=invitation.username)

    @priority.low
    def test_cannot_delete_not_existing_pending_invitation(self):
        """
        <b>Description:</b>
        Checks if not existing invitation cannot be removed from pending invitations list.

        <b>Input data:</b>
        1. User name.

        <b>Expected results:</b>
        Test passes when HTTP request deleting invitation returns status code 404 NOT FOUND.

        <b>Steps:</b>
        1. Try to delete not existing invitation.
        """
        step("Try to delete not existing invitation")
        username = "not_existing_user"
        invitation = Invitation(username=username)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     HttpStatus.MSG_NO_PENDING_INVITATION_FOR.format(username),
                                     invitation.api_delete)

    @priority.low
    def test_cannot_delete_pending_invitation_providing_empty_name(self):
        """
        <b>Description:</b>
        Checks if invitation cannot be removed from pending invitations list when an empty user name provided.

        <b>Input data:</b>
        1. User name.

        <b>Expected results:</b>
        Test passes when HTTP request deleting invitation returns status code 405 NOT ALLOWED.

        <b>Steps:</b>
        1. Delete invitation.
        """
        invitation = Invitation(username="")
        assert_raises_http_exception(HttpStatus.CODE_METHOD_NOT_ALLOWED,
                                     HttpStatus.MSG_METHOD_NOT_SUPPORTED.format("DELETE"),
                                     invitation.api_delete)

    @priority.medium
    def test_cannot_get_pending_invitations_as_non_admin_user(self, test_org_user_client):
        """
        <b>Description:</b>
        Checks if non-admin user cannot get pending invitations list.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when HTTP request to get pending invitations list returns status code 403 FORBIDDEN.

        <b>Steps:</b>
        1. As non admin user try to get pending invitations list.
        """
        step("As non admin user try to get pending invitations list")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_ACCESS_IS_DENIED,
                                     Invitation.api_get_list, test_org_user_client)
