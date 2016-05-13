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

import functools

from .. import gmail_api
from ..http_calls.platform import user_management as api
from ..test_names import generate_test_object_name
from ..tap_logger import get_logger


logger = get_logger(__name__)


@functools.total_ordering
class Invitation(object):

    def __init__(self, username, code=None):
        self.username = username
        self.code = code

    def __repr__(self):
        return "Invitation (username={})".format(self.username)

    def __eq__(self, other):
        return self.username == other.username

    def __lt__(self, other):
        return self.username < other.username

    @classmethod
    def api_send(cls, context, username=None, inviting_client=None):
        """Send invitation to a new user using inviting_client."""
        username = generate_test_object_name(email=True) if username is None else username
        response = api.api_invite_user(username, client=inviting_client)
        try:
            code = gmail_api.extract_code_from_message(response["details"])
        except AssertionError:  # Not all responses include code
            code = None
        invitation = cls(username=username, code=code)
        context.invitations.append(invitation)
        return invitation

    @classmethod
    def api_get_list(cls, client=None):
        """Return a list of pending invitations"""
        pending_invites = []
        for username in api.api_get_invitations(client=client):
            invite = cls(username=username)
            pending_invites.append(invite)
        return pending_invites

    def api_resend(self, client=None):
        api.api_resend_invitation(email=self.username, client=client)

    def api_delete(self, client=None):
        api.api_delete_invitation(email=self.username, client=client)

    def cleanup(self):
        self.api_delete()
