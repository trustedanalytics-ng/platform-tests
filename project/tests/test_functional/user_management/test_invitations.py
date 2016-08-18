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
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Invitation, User
from modules.tap_object_model.flows import onboarding
from tests.fixtures.assertions import assert_in_with_retry, assert_not_in_with_retry, assert_user_in_org_and_roles, \
    assert_raises_http_exception

logged_components = (TAP.user_management,)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestPendingInvitations:

    @priority.high
    def test_add_new_pending_invitation(self, context):
        step("Invite new user")
        invitation = Invitation.api_send(context)
        step("Check that the user is in the pending invitation list")
        assert_in_with_retry(invitation, Invitation.api_get_list)

    @priority.medium
    def test_accepting_invitation_deletes_it_from_pending_list(self, context):
        step("Invite new user")
        invitation = Invitation.api_send(context)
        step("Register user with the received code")
        onboarding.register(context, code=invitation.code, username=invitation.username)
        step("Check that invitation is no longer present in pending invitation list")
        assert_not_in_with_retry(invitation, Invitation.api_get_list)

    @priority.medium
    def test_add_new_pending_invitation_twice_for_the_same_user(self, context):
        step("Send invitation two times for a single user")
        invitation = Invitation.api_send(context)
        Invitation.api_send(context, username=invitation.username)
        invited_users = [i.username for i in Invitation.api_get_list()]
        step("Check that there is only one invitation for the user")
        assert invited_users.count(invitation.username) == 1, "More than one invitation for the user"

    @priority.medium
    def test_resend_pending_invitation(self, context):
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
        user, org = onboarding.register(context, code=invitation.code, username=invitation.username)
        assert_user_in_org_and_roles(user, org.guid, User.ORG_ROLES["manager"])

    @priority.low
    def test_cannot_resend_not_existing_pending_invitation(self):
        username = "not_existing_user"
        invitation = Invitation(username=username)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     HttpStatus.MSG_NO_PENDING_INVITATION_FOR.format(username),
                                     invitation.api_resend)

    @priority.low
    def test_cannot_resend_invitation_providing_empty_name(self):
        invitation = Invitation(username="")
        assert_raises_http_exception(HttpStatus.CODE_METHOD_NOT_ALLOWED,
                                     HttpStatus.MSG_METHOD_NOT_SUPPORTED.format("POST"),
                                     invitation.api_resend)

    @priority.medium
    def test_delete_pending_invitation(self, context):
        step("Invite new user")
        invitation = Invitation.api_send(context)
        assert_in_with_retry(invitation, Invitation.api_get_list)
        step("Delete pending user invitation")
        invitation.api_delete()
        assert_not_in_with_retry(invitation, Invitation.api_get_list)
        step("Check that the user cannot register after deletion of pending invitation")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_EMPTY,
                                     onboarding.register, context, code=invitation.code,
                                     username=invitation.username)

    @priority.low
    def test_cannot_delete_not_existing_pending_invitation(self):
        step("Try to delete not existing invitation")
        username = "not_existing_user"
        invitation = Invitation(username=username)
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     HttpStatus.MSG_NO_PENDING_INVITATION_FOR.format(username),
                                     invitation.api_delete)

    @priority.low
    def test_cannot_delete_pending_invitation_providing_empty_name(self):
        invitation = Invitation(username="")
        assert_raises_http_exception(HttpStatus.CODE_METHOD_NOT_ALLOWED,
                                     HttpStatus.MSG_METHOD_NOT_SUPPORTED.format("DELETE"),
                                     invitation.api_delete)

    @priority.medium
    def test_cannot_get_pending_invitations_as_non_admin_user(self, test_org_manager_client):
        step("As non admin user try to get pending invitations list")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_ACCESS_DENIED,
                                     Invitation.api_get_list, test_org_manager_client)
