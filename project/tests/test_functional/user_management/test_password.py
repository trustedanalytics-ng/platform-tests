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

from config import uaa_url
from modules import gmail_api, api_password
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import User
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.auth_gateway, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.user_management)]


class TestPassword:
    NEW_PASSWORD = "NEW_PASSWORD"

    @pytest.fixture(scope="function", autouse=True)
    def user(self, request, test_org, context):
        step("Create test user")
        self.test_user = User.create_by_adding_to_organization(context=context, org_guid=test_org.guid)

    @priority.high
    def test_reset_password(self):
        step("Login to the platform")
        client = self.test_user.get_client()
        pswd_api = api_password.PasswordAPI(self.test_user.username, self.test_user.password)

        step("Logout")
        client.request(method=HttpMethod.GET, url=uaa_url, path="logout")

        step("Enter your email and press  'SEND RESET PASSWORD LINK'")
        pswd_api.reset_password()

        step("Try to login with old credentials. User should still be able to login after pressing RESET")
        client.auth.authenticate()

        step("Logout and go to email message and press 'reset your password' link.")
        client.request(method=HttpMethod.GET, url=uaa_url, path="logout")
        code = gmail_api.get_reset_password_links(self.test_user.username)

        step("Enter new password twice and press 'CREATE NEW PASSWORD'.")
        pswd_api.reset_password_set_new(code, self.NEW_PASSWORD)

        step("Logout")
        client.request(method=HttpMethod.GET, url=uaa_url, path="logout")

        step("Try to login with old credentials.")
        assert_raises_http_exception(HttpStatus.CODE_OK, HttpStatus.MSG_INCORRECT_PASSWORD, self.test_user.login)

        step("Login to the platform with new credentials.")
        self.test_user.password = self.NEW_PASSWORD
        self.test_user.login()

    @priority.high
    def test_change_password(self):
        step("Login to the platform")
        client = self.test_user.get_client()
        self.test_user.login()

        step("Change user password.")
        pswd_api = api_password.PasswordAPI(self.test_user.username, self.test_user.password)
        pswd_api.change_password(self.test_user.password, self.NEW_PASSWORD)

        step("Logout and try to login with old credentials.")
        client.request(method=HttpMethod.GET, url=uaa_url, path="logout")
        HttpClientFactory.remove(self.test_user.client_configuration)
        assert_raises_http_exception(HttpStatus.CODE_OK, HttpStatus.MSG_INCORRECT_PASSWORD, self.test_user.login)

        step("Login to the platform with new credentials.")
        self.test_user.password = self.NEW_PASSWORD
        self.test_user.login()
