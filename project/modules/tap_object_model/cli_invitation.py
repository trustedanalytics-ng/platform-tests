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


class CliInvitation:

    def __init__(self, tap_cli, username, code=None):
        self.tap_cli = tap_cli
        self.username = username
        self.code = code

    def __repr__(self):
        return "CliInvitation (username={})".format(self.username)

    def __eq__(self, other):
        return self.username == other.username

    def __lt__(self, other):
        return self.username < other.username

    @classmethod
    def send(cls, context, tap_cli, username):
        tap_cli.invite(username)
        new_invitation = cls(tap_cli, username)
        context.invitations.append(new_invitation)
        return new_invitation

    def resend(self):
        self.tap_cli.reinvite(self.username)

    @classmethod
    def get_list(cls, tap_cli):
        output = tap_cli.invitations()
        pending_invitations = []
        for line in output.split("\n"):
            match = re.search("^([a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]+)$", line)
            if match:
                pending_invitations.append(cls(tap_cli=tap_cli, username=match.group(0)))
        return pending_invitations

    def delete(self, short_cmd=False):
        self.tap_cli.delete_invitation(self.username, short=short_cmd)

    def cleanup(self):
        self.delete()

