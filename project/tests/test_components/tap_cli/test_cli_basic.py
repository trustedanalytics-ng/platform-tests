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
from modules.tap_logger import step


class TestCliBasicFlow:
    @pytest.fixture(scope="function")
    def restore_login(self, request, tap_cli):
        request.addfinalizer(tap_cli.login)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_target(self, tap_cli, cli_login):
        step("Run tap target")
        output = tap_cli.target()
        assert config.cf_api_url in output
        assert config.ng_k8s_service_auth_username in output

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_help(self, tap_cli, cli_login):
        step("Check output from tap cli help")
        output = tap_cli.help()
        assert "USAGE" in output
        assert "VERSION" in output
        assert "COMMANDS" in output
        assert "GLOBAL OPTIONS" in output

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    @pytest.mark.bugs("DPNG-10167 [TAP-NG] CLI - help improvements required")
    def test_version(self, tap_cli, cli_login):
        step("Check tap cli version")
        output = tap_cli.version()
        match = re.search(r"TAP CLI version \d+\.\d+\.\d+", output)
        assert match is not None
        assert "0.0.0" not in output

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_cannot_login_with_incorrect_password(self, tap_cli, restore_login):
        step("Check that login with incorrect password returns Unauthorized")
        output = tap_cli.login(tap_auth=(config.ng_k8s_service_auth_username, "wrong"))
        assert 'CODE: 401 BODY: {"message":"Bad response status: 401"}\nAuthentication failed' in output

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")    
    @pytest.mark.bugs("DPNG-10120 [TAP-NG] CLI - ./tap target should be enable only for console-service ip")
    def test_cannot_login_with_incorrect_domain(self, tap_cli, restore_login):
        step("Check that user cannot login to tap cli using incorrect domain")
        inorrect_domain = "incorrect.domain"
        tap_cli.login(login_domain=inorrect_domain)
        output = tap_cli.target()
        assert inorrect_domain not in output
