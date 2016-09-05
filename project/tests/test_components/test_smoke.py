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
from modules.constants import TapComponent as TAP
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider, \
    ProxiedConfigurationProvider, ApiServiceConfigurationProvider
from modules.markers import priority
from modules.tap_logger import step
from tap_ng_component_config import k8s_core_services, third_party_services, api_service


@priority.high
@pytest.mark.usefixtures("open_tunnel")
class TestSmoke:
    k8s_core_service_params = sorted(k8s_core_services.items(), key=lambda x: x[0])
    k8s_core_service_ids = sorted([c for c in k8s_core_services.keys()])
    third_party_service_params = sorted(third_party_services.items(), key=lambda x: x[0])
    third_party_service_ids = sorted([c for c in third_party_services.keys()])

    def get_client(self, service_name, endpoint=None):
        configuration = K8sServiceConfigurationProvider.get(service_name, api_endpoint=endpoint)
        return HttpClientFactory.get(configuration)

    def get_proxied_client(self, url):
        configuration = ProxiedConfigurationProvider.get("http://{}".format(url))
        return HttpClientFactory.get(configuration)

    @pytest.mark.parametrize("service,service_params", k8s_core_service_params, ids=k8s_core_service_ids)
    def test_k8s_component_health_check(self, service, service_params):
        if service_params["health_endpoint"] is None:
            pytest.skip("Service {} does not have health endpoint configured".format(service))
        step("Check k8s component healtz endpoint for {}".format(service))
        health_client = self.get_client(service)
        response = health_client.request(HttpMethod.GET,
                                         path=service_params["health_endpoint"],
                                         raw_response=True,
                                         raise_exception=True,
                                         msg="get healthz")
        assert response.status_code == HttpStatus.CODE_OK

    def test_api_service_check_availability(self):
        step("Check api get endpoint for {}".format(TAP.api_service))
        api_client = HttpClientFactory.get(ApiServiceConfigurationProvider.get())
        response = api_client.request(HttpMethod.GET,
                                      path=api_service[TAP.api_service]["get_endpoint"],
                                      raw_response=True, raise_exception=True,
                                      msg="get")
        assert response.status_code == HttpStatus.CODE_OK

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

    @pytest.mark.parametrize("service,service_params", third_party_service_params, ids=third_party_service_ids)
    def test_3rd_party_component_check_availability(self, service, service_params):
        if service_params["get_endpoint"] is None or service_params["api_version"] is None:
            pytest.skip("Service {} does not have get endpoint or api version configured".format(service))
        step("Check 3rd party component get api endpoint for {}".format(service))
        health_client = self.get_proxied_client("{}/{}".format(service_params["url"],
                                                               service_params["api_version"]))
        response = health_client.request(HttpMethod.GET,
                                         path=service_params["get_endpoint"],
                                         raw_response=True,
                                         raise_exception=True, msg="get")
        assert response.status_code == HttpStatus.CODE_OK
