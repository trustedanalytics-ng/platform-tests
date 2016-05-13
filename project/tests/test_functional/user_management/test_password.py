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

from modules import gmail_api, api_password
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.tap_object_model import User


logged_components = (TAP.auth_gateway, TAP.auth_proxy, TAP.user_management)
pytestmark = [components.user_management]


class Password(TapTestCase):

    NEW_PASSWORD = "NEW_PASSWORD"

    @pytest.fixture(scope="function", autouse=True)
    def user(self, request, test_org, context):
        self.step("Create test user")
        self.test_user = User.api_create_by_adding_to_organization(context, org_guid=test_org.guid)

    @priority.high
    def test_reset_password(self):

        self.step("Login to the platform")
        client = self.test_user.get_client()
        pswd_api = api_password.PasswordAPI(client)

        self.step("Logout")
        client.logout()

        self.step("Enter your email and press  'SEND RESET PASSWORD LINK'")
        pswd_api.reset_password()

        self.step("Try to login with old credentials. User should still be able to login after pressing RESET")
        client.authenticate(self.test_user.password)

        self.step("Logout and go to email message and press 'reset your password' link.")
        client.logout()
        code = gmail_api.get_reset_password_links(self.test_user.username)

        self.step("Enter new password twice and press 'CREATE NEW PASSWORD'.")
        pswd_api.reset_password_set_new(code, self.NEW_PASSWORD)

        self.step("Logout")
        client.logout()

        self.step("Try to login with old credentials.")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_OK, HttpStatus.MSG_EMPTY, self.test_user.login)

        self.step("Login to the platform with new credentials.")
        self.test_user.password=self.NEW_PASSWORD
        self.test_user.login()

    @priority.high
    def test_change_password(self):
        self.step("Login to the platform")
        client = self.test_user.get_client()
        self.test_user.login()

        pswd_api = api_password.PasswordAPI(client)

        pswd_api.change_password(self.test_user.password, self.NEW_PASSWORD)

        self.step("Logout and try to login with old credentials.")
        client.logout()
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_OK, HttpStatus.MSG_EMPTY, self.test_user.login)

        self.step("Login to the platform with new credentials.")
        self.test_user.password=self.NEW_PASSWORD
        self.test_user.login()



