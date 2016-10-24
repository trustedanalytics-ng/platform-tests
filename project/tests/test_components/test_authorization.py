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
from modules.http_client import HttpClientFactory, HttpClientConfiguration, HttpClientType
from modules.http_calls.platform import api_service as api
from modules.markers import priority
from modules.tap_logger import step
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.api_service, )
pytestmark = [pytest.mark.components(TAP.api_service)]


class TestApiServiceAuthorization:

    @property
    def basic_auth_client(self):
        credentials = config.ng_k8s_service_credentials()
        configuration = HttpClientConfiguration(
            HttpClientType.BASIC_AUTH,
            url=config.api_url_full,
            username=credentials[0],
            password=credentials[1]
        )
        return HttpClientFactory.get(configuration)

    @priority.high
    def test_cannot_get_catalog_with_basic_auth(self):
        step("Check that basic auth does not work with api service")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_UNAUTHORIZED, ApiServiceHttpStatus.MSG_UNAUTHORIZED,
                                     api.get_offerings, client=self.basic_auth_client)
