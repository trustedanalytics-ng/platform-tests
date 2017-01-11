#
# Copyright (c) 2017 Intel Corporation
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

from modules.constants import TapComponent as TAP
from modules.http_client.http_client_type import HttpClientType
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.configuration_provider.k8s_service import ServiceConfigurationProvider
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import User
from tap_component_config import api_service
from tests.fixtures.assertions import assert_raises_command_execution_exception

pytestmark = [pytest.mark.components(TAP.cli), pytest.mark.components(TAP.api_service),
              pytest.mark.components(TAP.uaa)]


@pytest.mark.skipif(config.external_protocol != "https", reason="Test works only for environment with external ssl")
class TestSsl:
    HTTP_EXTERNAL_PROTOCOL = "http"
    UAA_LOGIN_URL_FORMAT = "{}://uaa.{}/login"
    API_LOGIN_URL_FORMAT = "{}://{}/api/{}/login{}"
    TAP_CLI_API_LOGIN_URL_FORMAT = "{}://{}"
    GET_URL_MESSAGE = "Get {}"

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def user(cls, test_org, class_context):
        step("Create test user")
        cls._test_user = User.create_by_adding_to_organization(context=class_context, org_guid=test_org.guid)

    @classmethod
    def get_client(cls, client_type):
        if client_type == HttpClientType.K8S_SERVICE:
            client_configuration = ServiceConfigurationProvider.get(username=cls._test_user.username,
                                                                    password=cls._test_user.password)
        else:
            client_configuration = ConsoleConfigurationProvider.get(username=cls._test_user.username,
                                                                    password=cls._test_user.password)

        client = HttpClientFactory.get(client_configuration)
        return client_configuration, client

    @priority.low
    def test_http_redirection_login_uaa(self):
        """
        <b>Description:</b>
        Checks if http get login uaa request is redirected to https

        <b>Input data:</b>
        Client: test user

        <b>Expected results:</b>
        Test passes when user is redirected to https page.

        <b>Steps:</b>
        1. Get console client and configuration.
        2. Log out from the console.
        3. Get login uaa page using http.
        4. Check https redirection.
        """
        step("Get console client and configuration")
        client_configuration, client = self.get_client(HttpClientType.CONSOLE)
        step("Log out from the platform")
        client.request(method=HttpMethod.GET, url=config.uaa_url, path="logout")
        HttpClientFactory.remove(client_configuration)
        step("Get login page using http")
        uaa_login_url = self.UAA_LOGIN_URL_FORMAT.format(self.HTTP_EXTERNAL_PROTOCOL, config.tap_domain)
        response = client.request(
            method=HttpMethod.GET,
            url=uaa_login_url,
            path="",
            raw_response=True
        )
        step("Check https redirection")
        assert response.url == self.UAA_LOGIN_URL_FORMAT.format(config.external_protocol, config.tap_domain)

    @priority.low
    def test_http_redirection_login_api_service(self):
        """
        <b>Description:</b>
        Checks if http get login api service request is redirected to https

        <b>Input data:</b>
        Client: test user

        <b>Expected results:</b>
        Test passes when user is redirected to https page.

        <b>Steps:</b>
        1. Get api service client and configuration.
        2. Get login api service page using http.
        3. Check https redirection.
        """
        step("Get api service client and configuration")
        client_configuration, client = self.get_client(HttpClientType.K8S_SERVICE)
        step("Get login page using http")
        api_version = api_service[TAP.api_service]["api_version"]
        default_url = self.API_LOGIN_URL_FORMAT.format(self.HTTP_EXTERNAL_PROTOCOL, config.api_url, api_version, "")
        credentials = config.ng_k8s_service_credentials()
        response = client.request(
            method=HttpMethod.GET,
            url=default_url,
            path="",
            headers={"Accept": "application/json"},
            credentials=credentials,
            raw_response=True
        )
        step("Check https redirection")
        assert response.url == self.API_LOGIN_URL_FORMAT.format(config.external_protocol, config.api_url, api_version,
                                                                "/")

    @pytest.mark.bugs("DPNG-15269 no redirection to https for tap-cli login http")
    @priority.low
    def test_http_redirection_login_tap_cli(self, tap_cli):
        """
        <b>Description:</b>
        Checks if tap cli http login request is redirected to https

        <b>Input data:</b>
        No input data

        <b>Expected results:</b>
        Test passes when there is redirection to https login page in output info.

        <b>Steps:</b>
        1. Try log in to platform using tap cli http login command in verbose mode INFO
        """
        step("Check that https redirection is displayed in output INFO")
        output = tap_cli.login(external_protocol=self.HTTP_EXTERNAL_PROTOCOL)
        get_https_message = self.GET_URL_MESSAGE.format(self.TAP_CLI_API_LOGIN_URL_FORMAT
                                                        .format(config.external_protocol, config.api_url))
        assert get_https_message in output
