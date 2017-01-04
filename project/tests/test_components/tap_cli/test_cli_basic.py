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

    INCORRECT_DOMAIN = 'www.incorrect.domain'
    FOREIGN_DOMAIN = 'www.google.com'

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
        assert tap_cli.CREATE_SERVICE[0] in output
        assert tap_cli.DELETE_SERVICE[0] in output
        assert tap_cli.SERVICE in output
        assert tap_cli.LOGS[0] in output
        assert tap_cli.PUSH in output
        assert tap_cli.APP[0] in output
        assert tap_cli.APPS[0] in output
        assert tap_cli.START in output
        assert tap_cli.STOP in output
        assert tap_cli.SCALE in output
        assert tap_cli.DELETE in output
        assert tap_cli.BINDINGS in output
        assert tap_cli.BIND[0] in output
        assert tap_cli.UNBIND[0] in output
        assert tap_cli.INVITE in output
        assert tap_cli.REINVITE in output
        assert tap_cli.USERS in output
        assert tap_cli.INVITATIONS[0] in output
        assert tap_cli.DELETE_INVITATION[0] in output
        assert tap_cli.DELETE_USER[0] in output

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
        assert_raises_command_execution_exception(1, TapMessage.NO_SUCH_HOST,
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
