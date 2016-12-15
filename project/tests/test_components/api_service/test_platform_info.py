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
import json

import config
from modules.constants import ApiServiceHttpStatus
from modules.http_client import HttpClientFactory, HttpClientConfiguration, HttpClientType, HttpMethod
from modules.tap_logger import step
from modules.http_calls.platform import api_service

class TestApiServicePlatformInfo:
    def test_get_platform_info(self, api_service_admin_client):
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
