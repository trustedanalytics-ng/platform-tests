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

from modules.http_client import HttpClientFactory, HttpClientConfiguration, HttpClientType, HttpMethod
from modules.tap_logger import step
from modules.http_calls.platform import api_service

class TestApiServicePlatformInfo:
    def test_get_platform_info(self, api_service_admin_client):
        """
        <b>Description:</b>
        Attempts retrieve platform info

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        - It's possible to retrieve platform info
        - The platform info has all the required fields

        <b>Steps:</b>
        - Log in as admin
        - platform info is retrieved by api service
        - verify returned response has all needed fields
        """
        step("Retrieve the platform info")
        response = api_service.get_platform_info(client=api_service_admin_client)
        assert "api_endpoint" in response
        assert "cli_version" in response
        assert "cli_url" in response
        assert "platform_version" in response
        assert "core_organization" in response
        assert "external_tools" in response
        assert "cdh_version" in response
        assert "k8s_version" in response
