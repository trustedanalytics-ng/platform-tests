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

from modules.http_calls.platform import api_service
from modules.markers import priority
from modules.tap_logger import step


@priority.high
class TestApiServiceResources:

    @pytest.mark.parametrize("resource", ["linux32", "linux64", "windows32", "macosx64"])
    def test_api_resource_cli_returns_tap_cli_binary(self, api_service_admin_client, resource):
        """
        <b>Description:</b>
        Checks if api resource CLI endpoint returns TAP CLI binary.

        <b>Input data:</b>
        1. Component name: api service.

        <b>Expected results:</b>
        Test passes when api resource CLI endpoint contains HTTP response headers:
        Content-Type, Content-Length, Content-Disposition

        <b>Steps:</b>
        1. Create HTTP client.
        2. Send GET request to component api endpoint.
        3. Verify that HTTP response contains headers: Content-Type, Content-Length, Content-Disposition.
        4. Verify that HTTP response content length equals to the one returned in Content-Length header.
        """
        step("Check get {} CLI resource".format(resource))
        response = api_service.get_cli_resource(client=api_service_admin_client, resource_id=resource)
        step('Check if response contains "Content-Type" header')
        assert response.headers['Content-Type'] == 'application/octet-stream'
        step('Check if response contains "Content-Length" header')
        content_length = int(response.headers['Content-Length'])
        assert content_length > 0
        step('Check if response contains "Content-Disposition" header')
        assert "tap" in response.headers['Content-Disposition']
        step('Check if response content length equals to the content length from header')
        assert len(response.content) == content_length
