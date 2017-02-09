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

import pytest

import config
from modules.constants import TapMessage, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from tests.fixtures.assertions import assert_raises_command_execution_exception


pytestmark = [pytest.mark.components(TAP.cli)]


class TestCliBasicFlow:

    INCORRECT_DOMAIN = 'www.incorrect.domain.com'
    FOREIGN_DOMAIN = 'www.wp.pl'

    @pytest.fixture(scope="function")
    def restore_login(self, request, tap_cli):
        request.addfinalizer(tap_cli.login)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    @priority.high
    def test_info(self, tap_cli, cli_login):
        """
        <b>Description:</b>
        Check that command 'info' prints proper credentials

        <b>Input data:</b>
        1. Command name: info
        2. TAP domain api address
        3. Username

        <b>Expected results:</b>
        Test passes when Tap CLI 'info' command returns proper credentials.

        <b>Steps:</b>
        1. Run TAP CLI with command 'info'.
        2. Verify response contains expected address.
        3. Verify response contains expected username.
        """
        step("Run tap info")
        output = tap_cli.info()
        assert config.cf_api_url in output
        assert config.admin_username in output

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    @priority.medium
    def test_help(self, tap_cli, cli_login):
        """
        <b>Description:</b>
        Check that command 'help' print a list of commands.

        <b>Input data:</b>
        1. Command name: help

        <b>Expected results:</b>
        Test passes when TAP CLI 'help' command show a list of commands.

        <b>Steps:</b>
        1. Run TAP CLI with command 'help'.
        2. Verify response contains expected headers.
        3. Verify response contains expected commands.
        """
        step("Check output from tap cli help")
        output = tap_cli.help()
        assert "USAGE" in output
        assert "VERSION" in output
        assert "COMMANDS" in output
        assert "GLOBAL OPTIONS" in output
        assert tap_cli.INFO in output
        assert tap_cli.HELP[0] in output
        assert tap_cli.VERSION[0] in output
        assert tap_cli.LOGIN in output
        assert tap_cli.LIST_OFFERINGS[0] in output
        assert tap_cli.SERVICE in output
        assert tap_cli.APPLICATION in output
        assert tap_cli.USERS[0] in output

        output = tap_cli.user_help()
        assert tap_cli.USERS[1] in output
        assert tap_cli.DELETE_USER[1] in output
        assert tap_cli.INVITATIONS[1] in output

        output = tap_cli.invitation_help()
        assert tap_cli.INVITATIONS[2] in output
        assert tap_cli.DELETE_INVITATION[2] in output
        assert tap_cli.INVITE[2] in output
        assert tap_cli.REINVITE[2] in output

        output = tap_cli.offering_help()
        assert tap_cli.CREATE_OFFERING[1] in output
        assert tap_cli.LIST_OFFERINGS[1] in output
        assert tap_cli.DELETE_OFFERING[1] in output

        output = tap_cli.service_binding_help()
        assert tap_cli.BINDING_CREATE[1] in output
        assert tap_cli.BINDING_DELETE[1] in output
        assert tap_cli.BINDING_LIST[1] in output

        output = tap_cli.application_binding_help()
        assert tap_cli.BINDING_CREATE[1] in output
        assert tap_cli.BINDING_DELETE[1] in output
        assert tap_cli.BINDING_LIST[1] in output

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    @priority.low
    def test_version(self, tap_cli, cli_login):
        """
        <b>Description:</b>
        Check TAP CLI command 'version' print the version

        <b>Input data:</b>
        1. Command name: version

        <b>Expected results:</b>
        Test passes when TAP CLI 'version' command print the version.

        <b>Steps:</b>
        1. Run TAP CLI with command version.
        2. Verify response print TAP CLI version in expected format.
        """
        step("Check tap cli version")
        output = tap_cli.version()
        match = re.search(r"TAP CLI version \d+\.\d+\.\d+", output)
        assert match is not None
        assert "0.0.0" not in output

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    @priority.low
    def test_cannot_login_with_incorrect_password(self, tap_cli, restore_login):
        """
        <b>Description:</b>
        Check that TAP CLI can't login with incorrect password and corresponding information is shown.

        <b>Input data:</b>
        1. Command name: login
        2. Invalid password

        <b>Expected results:</b>
        Test passes when TAP CLI login with incorrect password returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command login.
        2. Verify that TAP CLI command login with incorrect password returns expected message.
        """
        step("Check that login with incorrect password returns Unauthorized")
        assert_raises_command_execution_exception(1, TapMessage.AUTHENTICATION_FAILED,
                                                  tap_cli.login,
                                                  tap_auth=(config.ng_k8s_service_auth_username, "wrong"))

    @priority.low
    def test_cannot_login_with_incorrect_domain(self, tap_cli, restore_login):
        """
        <b>Description:</b>
        Check that TAP CLI can't login with incorrect domain and corresponding information is shown.

        <b>Input data:</b>
        1. Command name: login
        2. Incorrect TAP domain address

        <b>Expected results:</b>
        Test passes when TAP CLI login with incorrect TAP domain returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command login.
        2. Verify that TAP CLI command login with incorrect domain returns expected message.
        """
        step("Check that user cannot login to tap cli using incorrect domain")
        assert_raises_command_execution_exception(1, TapMessage.DOMAIN_NOT_FOUND,
                                                  tap_cli.login, login_domain=self.INCORRECT_DOMAIN)

    @priority.low
    def test_cannot_login_with_foreign_domain(self, tap_cli, restore_login):
        """
        <b>Description:</b>
        Check that TAP CLI can't login to foreign domain and corresponding information is shown.

        <b>Input data:</b>
        1. Command name: login
        2. Foreign domain address

        <b>Expected results:</b>
        Test passes when TAP CLI login with foreign domain returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command login.
        2. Verify that TAP command login with foreign domain returns expected message.
        """
        step("Check that user cannot login to tap cli using foreign domain")
        assert_raises_command_execution_exception(1, TapMessage.CANNOT_REACH_API,
                                                  tap_cli.login, login_domain=self.FOREIGN_DOMAIN)

    @priority.medium
    def test_login_without_optional_password_parameter(self, tap_cli):
        """
        <b>Description:</b>
        Check that TAP CLI will ask for user password and use it to log the user in.

        <b>Input data:</b>
        1. Command name: login
        2. TAP domain api address
        3. Username

        <b>Expected results:</b>
        Test passes when TAP CLI prompts for password and logs the user in when proper password given.

        <b>Steps:</b>
        0. Logout
        1. Run TAP CLI with command login.
        2. Enter user password
        3. Verify that user is logged in using info command.
        """
        tap_cli.logout_by_deleting_credentials_file()

        step("Check that user will be promped for password when it is not given in login parameters")
        output = tap_cli.login_with_password_prompt()
        assert TapMessage.AUTHENTICATION_SUCCEEDED in output

        step("Check that user is logged in correctly")
        output = tap_cli.info()
        assert config.api_url in output
        assert config.admin_username in output

    @pytest.fixture(scope="class")
    def empty_parameter_test_cases(self, tap_cli):
        return {
            "empty_api": {
                "parameter": "--api",
                "command": [tap_cli.LOGIN, tap_cli.API_PARAM]},
            "empty_username": {
                "parameter": "--username",
                "command": [tap_cli.LOGIN, tap_cli.API_PARAM, "http://{}".format(config.api_url),
                            tap_cli.USERNAME_PARAM]},
            "empty_password": {
                "parameter": "--password",
                "command": [tap_cli.LOGIN, tap_cli.API_PARAM, "http://{}".format(config.api_url),
                            tap_cli.USERNAME_PARAM, config.admin_username, tap_cli.PASSWORD_PARAM]}
        }

    @priority.medium
    @pytest.mark.parametrize("test_case", ("empty_api", "empty_username", "empty_password"))
    def test_cannot_login_with_empty_parameter(self, test_case, empty_parameter_test_cases, tap_cli):
        """
        <b>Description:</b>
        Check that TAP CLI will fail to login with any of the following parameters empty: api, username, password.

        <b>Input data:</b>
        1. Command name: login
        2. any of --api, --username, --pasword parameters empty

        <b>Expected results:</b>
        Test passes when TAP CLI reports "Incorrect Usage"

        <b>Steps:</b>
        1. Run TAP CLI with command login with:
            a) --api
            b) --username
            c) --pasword
            parameter empty value
        2. Verify "Incorrect Usage" raported
        """
        step("Check that user will not be logged in with missing " +
             empty_parameter_test_cases[test_case]["parameter"] + " parameter value")
        assert_raises_command_execution_exception(
            1, TapMessage.INCORRECT_USAGE, tap_cli._run_command, empty_parameter_test_cases[test_case]["command"])

    @priority.medium
    def test_check_credentials_file(self, tap_cli):
        """
        <b>Description:</b>
        Check that TAP CLI stored user & environment info in ~/.tap-cli/credentials.json file.

        <b>Input data:</b>
        1. File path: ~/.tap-cli/credentials.json

        <b>Expected results:</b>
        The file contains api adress and username

        <b>Steps:</b>
        0. Logout
        1. Login
        2. Read the file and check for expected info.
        """
        step("Check that credentials.json file contains api adress and username after user successfully logged in")
        tap_cli.logout_by_deleting_credentials_file()

        step("login")
        tap_cli.login()

        step("check file content")
        file_content = tap_cli.read_credentials_file()
        assert config.api_url in file_content
        assert config.admin_username in file_content