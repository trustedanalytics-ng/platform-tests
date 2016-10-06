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
from modules.constants import TapComponent as TAP
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.application import ApplicationConfigurationProvider
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider, \
    ProxiedConfigurationProvider, ServiceConfigurationProvider
from modules.markers import priority
from modules.ssh_lib import JumpClient
from modules.tap_logger import step
from tap_component_config import TAP_core_services, third_party_services, api_service


@priority.high
@pytest.mark.usefixtures("open_tunnel")
class TestK8sComponents:
    k8s_core_service_params = sorted(TAP_core_services.items(), key=lambda x: x[0])
    k8s_core_service_ids = sorted([c for c in TAP_core_services.keys()])
    third_party_service_params = sorted(third_party_services.items(), key=lambda x: x[0])
    third_party_service_ids = sorted([c for c in third_party_services.keys()])

    @classmethod
    @pytest.fixture(scope="class")
    def running_tap_components(cls):
        component_name_list = []
        step("Retrieve tap components")
        jump_client = JumpClient(username=config.ng_jump_user)
        kubectl_output = jump_client.ssh("kubectl get services")
        for app in kubectl_output[2:]:
            name = app.split()[0]
            component_name_list.append(name)
        return component_name_list

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
        api_client = HttpClientFactory.get(ServiceConfigurationProvider.get())
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

    @pytest.mark.parametrize("expected_app", TAP.get_list())
    def test_k8s_component_presence_on_platform(self, expected_app, running_tap_components):
        step("Check that '{}' app is present on platform".format(expected_app))
        assert expected_app in running_tap_components


@priority.high
class TestSmokeTrustedAnalyticsComponents:

    @pytest.mark.parametrize("component", [TAP.user_management, TAP.api_service, TAP.uaa])
    def test_components_check_healthz(self, component):
        step("Check healthz endpoint")
        url = "http://{}.{}".format(component, config.tap_domain)
        client = HttpClientFactory.get(ApplicationConfigurationProvider.get(url))
        response = client.request(method=HttpMethod.GET, path="healthz", raw_response=True)
        assert response.status_code == HttpStatus.CODE_OK

    @pytest.mark.bugs("DPNG-11452 Healthz response returns 200 for non existing application")
    def test_components_check_healthz_anything(self):
        component = "anything"
        url = "http://{}.{}".format(component, config.tap_domain)
        client = HttpClientFactory.get(ApplicationConfigurationProvider.get(url))
        response = client.request(method=HttpMethod.GET, path="healthz", raw_response=True)
        assert response.status_code == HttpStatus.CODE_NOT_FOUND

    @pytest.mark.parametrize("component", [TAP.console])
    def test_components_root_endpoint(self, component):
        step("Check get / endpoint")
        url = "http://{}.{}".format(component, config.tap_domain)
        client = HttpClientFactory.get(ServiceConfigurationProvider.get(url))
        response = client.request(method=HttpMethod.GET, path="", raw_response=True)
        assert response.status_code == HttpStatus.CODE_OK