# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import pytest
from modules.constants import HttpStatus, TapComponent as TAP
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider
from modules.tap_logger import step

tested_components = [TAP.uploader, TAP.downloader, TAP.das, TAP.dataset_publisher, TAP.workflow_scheduler,
                     TAP.platform_snapshot, TAP.auth_gateway]


@pytest.mark.usefixtures("open_tunnel")
class TestComponentInfo:

    def get_client(self, service_name, endpoint=None):
        configuration = K8sServiceConfigurationProvider.get(service_name, api_endpoint=endpoint)
        return HttpClientFactory.get(configuration)

    @pytest.mark.parametrize("service", tested_components)
    def test_component_info_check(self, service):
        """
        <b>Description:</b>
        Checks if k8s core components info endpoint returns status OK and proper response message to HTTP GET request.

        <b>Input data:</b>
        TAP core components.

        <b>Expected results:</b>
        Test passes when k8s core components return status OK and proper response message to HTTP GET request on
         info endpoint.

        <b>Steps:</b>
        1. Check k8s component info endpoint.
        2. Verify that HTTP response status code is 200.
        3. Verify that HTTP response message is proper.
        """
        msg = ["\"name\":\"{}\"".format(service), "\"artifact\":\"{}\"".format(service), "app_version", "build",
               "group", "artifact", "version", "time", "git", "branch", "commit"]
        step("Check k8s component info endpoint for {}".format(service))
        health_client = self.get_client(service)
        response = health_client.request(HttpMethod.GET,
                                         path="info",
                                         raw_response=True,
                                         raise_exception=True,
                                         )
        assert response.status_code == HttpStatus.CODE_OK
        for item in msg:
            assert item in str(response.content)
