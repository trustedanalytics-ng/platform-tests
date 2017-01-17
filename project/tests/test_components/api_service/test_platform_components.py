#
# Copyright (c) 2016-2017 Intel Corporation
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

from modules.tap_logger import step
from modules.http_calls.platform import api_service

class TestApiServicePlatformComponents:
    def test_get_platform_components(self, api_service_admin_client):
        """
        <b>Description:</b>
        Attempts retrieve platform components

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        - It's possible to retrieve platform components
        - The platform info has all the required fields

        <b>Steps:</b>
        - Log in as admin
        - platform info is retrieved by api service
        - verify returned response has all needed fields
        """
        step("Retrieve the platform components")
        response = api_service.get_platform_components(client=api_service_admin_client)
        for k in response:
            assert "app_version" in k
            assert "signature" in k
            assert "imageVersion" in k
            assert "name" in k
