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

from modules import gmail_api, api_password
from modules.constants import TapComponent as TAP, UserManagementHttpStatus as HttpStatus
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, priority
from modules.tap_object_model import User


@log_components()
@components(TAP.user_management, TAP.auth_gateway, TAP.auth_proxy)
class PasswordTests(TapTestCase):

    NEW_PASSWORD = "NEW_PASSWORD"

    @classmethod
    @cleanup_after_failed_setup(User.cf_api_tear_down_test_users)
    def setUpClass(cls):
        cls.step("Create users for password tests")
        cls.users, _ = User.api_create_users_for_tests(2)

    @priority.high
    def test_reset_password(self):
        user = self.users.pop()

        self.step("Login to the platform")
        client = user.get_client()
        pswd_api = api_password.PasswordAPI(client)

        self.step("Logout")
        client.logout()

        self.step("Enter your email and press  'SEND RESET PASSWORD LINK'")
        pswd_api.reset_password()

        self.step("Try to login with old credentials. User should still be able to login after pressing RESET")
        client.authenticate(user.password)

        self.step("Logout and go to email message and press 'reset your password' link.")
        client.logout()
        code = gmail_api.get_reset_password_links(user.username)

        self.step("Enter new password twice and press 'CREATE NEW PASSWORD'.")
        pswd_api.reset_password_set_new(code, self.NEW_PASSWORD)

        self.step("Try to login with old credentials.")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_OK, HttpStatus.MSG_EMPTY, user.login)

        self.step("Login to the platform with new credentials.")
        user.password=self.NEW_PASSWORD
        user.login()

    @priority.high
    def test_change_pass(self):
        user = self.users.pop()

        self.step("Login to the platform")
        client = user.get_client()
        user.login()

        pswd_api = api_password.PasswordAPI(client)

        pswd_api.change_password(user.password, self.NEW_PASSWORD)

        self.step("Logout and try to login with old credentials.")
        client.logout()
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_OK, HttpStatus.MSG_EMPTY, user.login)

        self.step("Login to the platform with new credentials.")
        user.password=self.NEW_PASSWORD
        user.login()



