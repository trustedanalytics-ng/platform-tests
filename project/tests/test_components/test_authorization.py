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

import config
from modules.constants import ApiServiceHttpStatus, TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.http_client import HttpClientFactory, HttpClientConfiguration, HttpClientType, HttpMethod
from modules.http_calls.platform import api_service as api
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.markers import priority
from modules.tap_logger import step
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.api_service, )
pytestmark = [pytest.mark.components(TAP.api_service)]


class TestApiServiceAuthorization:

    @property
    def basic_auth_client(self):
        credentials = config.ng_k8s_service_credentials()
        configuration = HttpClientConfiguration(
            HttpClientType.BASIC_AUTH,
            url=config.api_url_full_v2,
            username=credentials[0],
            password=credentials[1]
        )
        return HttpClientFactory.get(configuration)

    @priority.high
    def test_cannot_get_catalog_with_basic_auth(self):
        step("Check that basic auth does not work with api service")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_UNAUTHORIZED, ApiServiceHttpStatus.MSG_UNAUTHORIZED,
                                     api.get_offerings, client=self.basic_auth_client)

    @priority.high
    def test_cannot_get_platform_info_with_basic_auth(self):
        step("Check that basic auth does not work with platform info")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_UNAUTHORIZED, ApiServiceHttpStatus.MSG_UNAUTHORIZED,
                                     api.get_platform_info, client=self.basic_auth_client)


    def test_login_to_console_with_valid_credentials(self):
        step("Login using uaa endpoint")
        client = HttpClientFactory.get(
            ConsoleConfigurationProvider.get(
                config.admin_username,
                config.admin_password))
        client.request(method=HttpMethod.GET, path="users/current")

    def test_login_to_console_with_invalid_credentials(self):
        step("Login using uaa endpoint")
        configuration = ConsoleConfigurationProvider.get(
                username=generate_test_object_name(separator=""),
                password=generate_test_object_name(separator=""))
        with pytest.raises(UnexpectedResponseError):
            HttpClientFactory.get(configuration)

    def test_login_to_console_with_empty_credentials(self):
        step("Login using uaa endpoint")
        configuration = ConsoleConfigurationProvider.get(
                username="",
                password="")
        with pytest.raises(UnexpectedResponseError):
            HttpClientFactory.get(configuration)

    def test_login_to_console_without_password(self):
        step("Login using uaa endpoint")
        configuration = ConsoleConfigurationProvider.get(
                username=config.admin_username,
                password=None)
        with pytest.raises(UnexpectedResponseError):
            HttpClientFactory.get(configuration)
