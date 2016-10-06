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

import json

from bs4 import BeautifulSoup

from config import uaa_url
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.console_no_auth import ConsoleNoAuthConfigurationProvider
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory


class PasswordAPI(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = HttpClientFactory.get(ConsoleNoAuthConfigurationProvider.get())

    @property
    def _username(self):
        return self.username

    def reset_password(self):
        self.client.request(
            method=HttpMethod.POST,
            url=uaa_url,
            path="forgot_password.do",
            data={"email": self._username},
            headers={"Accept": "text/html", "Content-Type": "application/x-www-form-urlencoded"},
            msg="Reset password"
        )

    def reset_password_set_new(self, code, new_password):
        new_code, csrf_code = self._get_codes(code)
        data = {
            "email": self._username,
            "code": new_code,
            "password": new_password,
            "password_confirmation": new_password,
            "_csrf": csrf_code,
        }
        self.client.request(
            method=HttpMethod.POST,
            url=uaa_url,
            path="reset_password.do",
            data=data,
            headers={"Accept": "text/html", "Content-Type": "application/x-www-form-urlencoded"},
            msg="Reset password: set new"
        )

    def _get_codes(self, code):
        response = self.client.request(
            method=HttpMethod.GET,
            url=uaa_url,
            path="reset_password?code={}&email={}".format(code, self._username),
            msg="Reset password: get reset form"
        )
        return self._parse_codes(response)

    @staticmethod
    def _parse_codes(message):
        soup = BeautifulSoup(message, 'html.parser')
        csrf_input = soup.find("input", attrs={"name": "_csrf"})
        if csrf_input is None:
            raise AssertionError("Can't find csrf code in given message: {}".format(message))
        code_input = soup.find("input", attrs={"name": "code"})
        if code_input is None:
            raise AssertionError("Can't find one-time code in given message: {}".format(message))
        return code_input['value'], csrf_input['value']

    def change_password(self, old_password, new_password):
        data = {
            "oldPassword": old_password,
            "password": new_password,
        }
        client = HttpClientFactory.get(ConsoleConfigurationProvider.get(
            self._username, old_password))
        client.request(
            method=HttpMethod.PUT,
            path="users/current/password",
            data=json.dumps(data),
            headers={"Accept": "application/json", "Content-Type": "application/json;charset=UTF-8"},
            msg="Change password"
        )
