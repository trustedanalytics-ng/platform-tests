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
from modules.constants import HttpStatus
from modules.exceptions import UnexpectedResponseError
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.application import ApplicationConfigurationProvider
from modules.markers import priority
from modules.tap_logger import step


@priority.high
class TestTrustedAnalyticsComponents:

    def test_calling_healthz_on_non_existing_service_returns_404(self):
        """
        <b>Description:</b>
        Checks if calling healthz endpoint on not existing service returns error status code 404.

        <b>Input data:</b>
        False service URL.

        <b>Expected results:</b>
        Test passes when not existing service healthz endpoint returns status code 404 to HTTP GET request.

        <b>Steps:</b>
        1. Check healthz endpoint for not existing service.
        2. Verify that response status code is 404.
        """
        expected_status_code = HttpStatus.CODE_NOT_FOUND
        url = "http://anything.{}".format(config.tap_domain)
        step("Check that calling {} returns {}".format(url, expected_status_code))
        client = HttpClientFactory.get(ApplicationConfigurationProvider.get(url))
        with pytest.raises(UnexpectedResponseError) as e:
            client.request(method=HttpMethod.GET, path="healthz")
        assert e.value.status == expected_status_code
