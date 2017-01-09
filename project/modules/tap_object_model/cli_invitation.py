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

from modules import test_names
from ._cli_object_superclass import CliObjectSuperclass


class CliInvitation(CliObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["name"]

    def __init__(self, *, tap_cli, username, code=None):
        super().__init__(tap_cli=tap_cli, name=username)
        self.code = code

    @classmethod
    def send(cls, context, *, tap_cli, username=None):
        if username is None:
            username = test_names.generate_test_object_name(email=True)
        tap_cli.login()
        tap_cli.invite(username)
        new_invitation = cls(tap_cli=tap_cli, username=username)
        context.test_objects.append(new_invitation)
        return new_invitation

    @classmethod
    def get_list(cls, tap_cli, short_cmd=False):
        output = tap_cli.invitations()
        pending_invitations = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', output)
        return [cls(tap_cli=tap_cli, username=invitation) for invitation in pending_invitations]

    def resend(self):
        self.tap_cli.reinvite(self.username)

    def delete(self, short_cmd=False):
        self.tap_cli.delete_invitation(self.name)
