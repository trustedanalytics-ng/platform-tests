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
from modules import gmail_api
from modules.tap_object_model.flows.onboarding import register


class CliUser:

    def __init__(self, tap_cli, username):
        self.tap_cli = tap_cli
        self.username = username

    def __repr__(self):
        return "CliUser (username={})".format(self.username)

    def __eq__(self, other):
        return self.username == other.username

    def __lt__(self, other):
        return self.username < other.username

    @classmethod
    def register(cls, context, invitation):
        code = gmail_api.get_invitation_code_for_user(invitation.username)
        user = register(context=context, code=code, username=invitation.username)
        cli_user = CliUser._from_user(invitation.tap_cli, user)
        context.users[-1] = cli_user
        return cli_user

    @classmethod
    def _from_user(cls, tap_cli, user):
        return cls(tap_cli=tap_cli, username=user.username)

    @classmethod
    def get_list(cls, tap_cli):
        output = tap_cli.users()
        return [cls(tap_cli, line) for line in output.split("\n")]

    def delete(self, short_cmd=False):
        self.tap_cli.delete_user(self.username, short=short_cmd)

    def cleanup(self):
        self.delete()
