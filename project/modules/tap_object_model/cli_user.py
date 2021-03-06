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
import functools

from modules import gmail_api
from modules.exceptions import UnexpectedResponseError
from modules.tap_object_model.flows import onboarding
from ._cli_object_superclass import CliObjectSuperclass


@functools.total_ordering
class CliUser(CliObjectSuperclass):
    _COMPARABLE_ATTRIBUTES = ["name"]

    def __init__(self, *, tap_cli, username):
        super().__init__(tap_cli=tap_cli, name=username)

    @classmethod
    def register(cls, context, *, org_guid, tap_cli, username):
        code = gmail_api.get_invitation_code_for_user(username)
        onboarding.register(context=context, code=code,
                            username=username, org_guid=org_guid)
        cli_user = cls(tap_cli=tap_cli, username=username)
        context.test_objects.append(cli_user)
        return cli_user

    @classmethod
    def get_list(cls, *, tap_cli):
        output = tap_cli.users()
        user_list = re.findall(r'[\w\.-@+]{3,}', output)
        return [cls(tap_cli=tap_cli, username=user) for user in user_list]

    def delete(self):
        if self._is_deleted is True:
            return

        try:
            self.tap_cli.delete_user(self.name)
            self._set_deleted(True)
        except UnexpectedResponseError:
            raise
