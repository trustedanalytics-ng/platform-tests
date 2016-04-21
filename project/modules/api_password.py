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
import json

from configuration import config


class PasswordAPI(object):

    def __init__(self, client):
        self.client = client

    @property
    def _username(self):
        return self.client.get_username()

    def reset_password(self):
        url = self.client.create_login_url("forgot_password.do")
        data = {"email": self._username}
        self.client.post(url, data, "reset password")

    def reset_password_set_new(self, code, new_password):
        csrf_code = self._get_csrf_code(code)

        url = self.client.create_login_url("reset_password.do")
        data = {"email": self._username, "code": code, "password": new_password,
              "password_confirmation": new_password, "_csrf": csrf_code}
        self.client.post(url, data, "reset password: set new")

    def _get_csrf_code(self, code):
        url = self.client.create_login_url("reset_password?code={}&email={}".format(code, self._username))
        data = self.client.get(url, "reset password: get reset form")
        return self._parse_csrf_code(data)

    @staticmethod
    def _parse_csrf_code(message):
        pattern = r"(?<=value=\")([a-zA-Z0-9]*[-][a-zA-Z0-9-]*)+"
        match = re.search(pattern, message)
        if match is None:
            raise AssertionError("Can't find code in given message: {}".format(message))
        return match.group()

    def change_password(self, old_password, new_password):
        url = "https://console.{}/{}".format(config.CONFIG["domain"], "rest/users/current/password")
        data = {"oldPassword": old_password, "password": new_password}
        self.client.put(url, json.dumps(data), "change password")
