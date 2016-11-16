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

from modules.constants import HttpStatus
from modules.http_client import HttpMethod
from modules.markers import priority
from modules.tap_logger import step
from tap_component_config import TAP_core_services


@priority.high
@pytest.mark.usefixtures("open_tunnel")
@pytest.mark.skip(reason="To be considered if this test is valid.")
class TestK8sComponents:

    k8s_core_service_params = sorted(TAP_core_services.items(), key=lambda x: x[0])
    k8s_core_service_ids = sorted([c for c in TAP_core_services.keys()])

    @pytest.mark.parametrize("service,service_params", k8s_core_service_params, ids=k8s_core_service_ids)
    def test_k8s_component_api_check_availability(self, service, service_params):
        if service_params["get_endpoint"] is None or service_params["api_version"] is None:
            pytest.skip("Service {} does not have get endpoint or api version configured".format(service))
        step("Check k8s component api get endpoint for {}".format(service))
        api_client = self.get_client(service, "api/{}".format(service_params["api_version"]))
        response = api_client.request(HttpMethod.GET,
                                      path=service_params["get_endpoint"],
                                      raw_response=True, raise_exception=True,
                                      msg="get")
        assert response.status_code == HttpStatus.CODE_OK

    @pytest.mark.parametrize("service,service_params", k8s_core_service_params, ids=k8s_core_service_ids)
    def test_k8s_component_api_check_version_alias(self, service, service_params):
        if service_params["get_endpoint"] is None or service_params["api_version_alias"] is None:
            pytest.skip("Service {} does not have get endpoint or api version alias configured".format(service))
        step("Check k8s component api get endpoint alias for {}".format(service))
        api_client = self.get_client(service, "api/{}".format(service_params["api_version_alias"]))
        response = api_client.request(HttpMethod.GET,
                                      path=service_params["get_endpoint"],
                                      raw_response=True, raise_exception=True,
                                      msg="get using version alias")
        assert response.status_code == HttpStatus.CODE_OK
