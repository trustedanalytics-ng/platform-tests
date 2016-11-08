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
import json

from modules.http_client import HttpClientFactory, HttpClientConfiguration, HttpClientType, HttpMethod
from modules.tap_logger import step
from modules.constants import TapComponent as TAP, ApiServiceHttpStatus
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.api_service, )
pytestmark = [pytest.mark.components(TAP.api_service)]


class TestApiServiceBasicFlow:
    MSG_NO_CREDENTIALS_PROVIDED = "{\"message\":\"No credentials provided\"}"
    MSG_INVALID_CREDENTIALS_PROVIDED = "{\"message\":\"Bad response status: 401\"}"
    KEY_ACCESS_TOKEN = "access_token"

    def _get_client(self, client_type=HttpClientType.BASIC_AUTH, username=None, password=None):
        configuration = HttpClientConfiguration(
            client_type=client_type,
            url=config.api_url_full_v2,
            username=username,
            password=password
        )
        return HttpClientFactory.get(configuration)

    def test_login_without_providing_credentials(self):
        step("Login without providing credentials")
        client = self._get_client(client_type=HttpClientType.NO_AUTH)
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST, self.MSG_NO_CREDENTIALS_PROVIDED,
                                     client.request, method=HttpMethod.GET, path="login", raw_response=True,
                                     msg="Login without credentials")

    def test_login_providing_invalid_credentials(self):
        step("Login providing invalid credentials")
        client = self._get_client(username=generate_test_object_name(), password=generate_test_object_name())

        assert_raises_http_exception(ApiServiceHttpStatus.CODE_UNAUTHORIZED, self.MSG_INVALID_CREDENTIALS_PROVIDED,
                                     client.request, method=HttpMethod.GET, path="login", raw_response=True,
                                     msg="Login with invalid credentials")

    def test_login_providing_valid_credentials(self):
        step("Login providing valid credentials")
        credentials = config.ng_k8s_service_credentials()
        client = self._get_client(username=credentials[0],
                                  password=credentials[1])
        response = client.request(method=HttpMethod.GET,
                                  path="login",
                                  raw_response=True,
                                  msg="Login with valid credentials")

        assert response.status_code == ApiServiceHttpStatus.CODE_OK
        assert self.KEY_ACCESS_TOKEN in response.text
        assert len(json.loads(response.text)[self.KEY_ACCESS_TOKEN]) > 0
