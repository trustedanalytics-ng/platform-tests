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
from modules.constants import HttpStatus, ServiceLabels, TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.application import ApplicationConfigurationProvider
from modules.http_client.configuration_provider.k8s_service import K8sServiceConfigurationProvider, \
    ProxiedConfigurationProvider, ServiceConfigurationProvider
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model.k8s_service import K8sService
from tap_component_config import TAP_core_services, third_party_services, api_service, offerings_as_parameters


not_tested_components = [TAP.das, TAP.data_catalog, TAP.dataset_publisher, TAP.downloader,
                        TAP.h2o_scoring_engine_publisher, TAP.metadata_parser, TAP.metrics_grafana,
                        TAP.metrics_prometheus, TAP.nginx_ingress, TAP.uploader]

not_tested_offerings = [ServiceLabels.H2O, ServiceLabels.HBASE, ServiceLabels.HDFS, ServiceLabels.HIVE,
                        ServiceLabels.JUPYTER, ServiceLabels.SCORING_ENGINE, ServiceLabels.SCORING_PIPELINES,
                        ServiceLabels.ZOOKEEPER]
filtered_offerings_as_parameters = list(filter(lambda x: x[0] not in not_tested_offerings, offerings_as_parameters))


@priority.high
@pytest.mark.usefixtures("open_tunnel")
class TestK8sComponents:
    k8s_core_service_params = list(filter(lambda x: x[0] not in not_tested_components,
                                          sorted(TAP_core_services.items(), key=lambda x: x[0])))
    k8s_core_service_ids = sorted([c for c in TAP_core_services.keys() if c not in not_tested_components])
    third_party_service_params = sorted(third_party_services.items(), key=lambda x: x[0])
    third_party_service_ids = sorted([c for c in third_party_services.keys()])

    @classmethod
    @pytest.fixture(scope="class")
    def running_tap_components(cls):
        step("Retrieve tap components")
        service_list = K8sService.get_list()
        return [service.name for service in service_list]

    def get_client(self, service_name, endpoint=None):
        configuration = K8sServiceConfigurationProvider.get(service_name, api_endpoint=endpoint)
        return HttpClientFactory.get(configuration)

    def get_proxied_client(self, url):
        configuration = ProxiedConfigurationProvider.get("http://{}".format(url))
        return HttpClientFactory.get(configuration)

    @pytest.mark.parametrize("service,service_params", k8s_core_service_params, ids=k8s_core_service_ids)
    def test_k8s_component_health_check(self, service, service_params):
        """
        <b>Description:</b>
        Checks if k8s core components healthz endpoint returns status OK to HTTP GET request.

        <b>Input data:</b>
        TAP core components.

        <b>Expected results:</b>
        Test passes when k8s core components return status OK to HTTP GET request on healthz endpoint.

        <b>Steps:</b>
        1. Check k8s component healthz endpoint.
        2. Verify that HTTP response status code is 200.
        """
        if service_params["health_endpoint"] is None:
            pytest.skip("Service {} does not have healthz endpoint configured".format(service))
        step("Check k8s component healthz endpoint for {}".format(service))
        health_client = self.get_client(service)
        response = health_client.request(HttpMethod.GET,
                                         path=service_params["health_endpoint"],
                                         raw_response=True,
                                         raise_exception=True,
                                         msg="get healthz")
        assert response.status_code == HttpStatus.CODE_OK

    def test_api_service_check_availability(self):
        """
        <b>Description:</b>
        Checks if api service is available.

        <b>Input data:</b>
        1. TAP domain name.

        <b>Expected results:</b>
        Test passes when platform api service returns OK status to HTTP GET request.

        <b>Steps:</b>
        1. Check api get endpoint for a domain.
        2. Verify that response status is OK.
        """
        step("Check api get endpoint for {}".format(TAP.api_service))
        api_client = HttpClientFactory.get(ServiceConfigurationProvider.get())
        response = api_client.request(HttpMethod.GET,
                                      path=api_service[TAP.api_service]["get_endpoint"],
                                      raw_response=True, raise_exception=True,
                                      msg="get")
        assert response.status_code == HttpStatus.CODE_OK

    @pytest.mark.parametrize("service,service_params", third_party_service_params, ids=third_party_service_ids)
    def test_3rd_party_component_check_availability(self, service, service_params):
        """
        <b>Description:</b>
        Checks if 3rd party component is available.

        <b>Input data:</b>
        1. List of third party components (currently: image repository).

        <b>Expected results:</b>
        Test passes when 3rd party component api service returns OK status to HTTP GET request.

        <b>Steps:</b>
        1. Check api get endpoint of 3rd party component.
        2. Verify that response status is OK.
        """
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

    @pytest.mark.parametrize("expected_app", list(filter(lambda x: x not in not_tested_components,
                                                         TAP.get_list_internal())))
    def test_k8s_component_presence_on_platform(self, expected_app, running_tap_components):
        """
        <b>Description:</b>
        Checks if k8s services are present on the platform.

        <b>Input data:</b>
        TAP core components.

        <b>Expected results:</b>
        Test passes when all k8s services are present on the platform.

        <b>Steps:</b>
        1. Verify that all k8s services are present on the platform.
        """
        step("Check that '{}' app is present on platform".format(expected_app))
        assert expected_app in running_tap_components, "No such service {}".format(expected_app)

    @pytest.mark.parametrize("expected_offering,plan_name", filtered_offerings_as_parameters)
    def test_available_offerings(self, expected_offering, plan_name, test_marketplace):
        """
        <b>Description:</b>
        Checks if marketplace official offerings are present on the platform.

        <b>Input data:</b>
        Offering names.

        <b>Expected results:</b>
        Test passes when marketplace official offerings are present on the platform.

        <b>Steps:</b>
        1. Verify that marketplace offerings are not None.
        2. Verify that marketplace offerings planes are not None.
        """
        offering = next((o for o in test_marketplace if o.label == expected_offering), None)
        assert offering is not None, "Offering '{}' was not found in marketplace".format(expected_offering)
        plan_name = next((plan for plan in offering.service_plans if plan.name == plan_name), None)
        assert plan_name is not None, "Plan '{}' for offering '{}' was not found".format(plan_name, expected_offering)


@priority.high
class TestSmokeTrustedAnalyticsComponents:

    @pytest.mark.bugs("DPNG-13413 user-management is no longer reachable from outside network")
    @pytest.mark.parametrize("component", [TAP.api_service, TAP.uaa])
    def test_components_check_healthz(self, component):
        """
        <b>Description:</b>
        Checks if user-management, api service and uaa return status OK on healthz endpoint.

        <b>Input data:</b>
        1. Component names: user-management, api service, uaa.

        <b>Expected results:</b>
        Test passes when user-management, api service and uaa healthz endpoint return status OK to HTTP GET request.

        <b>Steps:</b>
        1. Check healthz endpoint for components: user-management, api service and uaa.
        2. Verify that response status is OK.
        """
        step("Check healthz endpoint")
        url = "http://{}.{}".format(component, config.tap_domain)
        client = HttpClientFactory.get(ApplicationConfigurationProvider.get(url))
        response = client.request(method=HttpMethod.GET, path="healthz", raw_response=True)
        assert response.status_code == HttpStatus.CODE_OK

    @pytest.mark.bugs("DPNG-11452 Healthz response returns 200 for non existing application")
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

    @pytest.mark.parametrize("component", [TAP.console])
    def test_components_root_endpoint(self, component):
        """
        <b>Description:</b>
        Checks if console root endpoint returns OK status to HTTP GET request.

        <b>Input data:</b>
        Component root endpoint.

        <b>Expected results:</b>
        Test passes when console root endpoint returns OK status to HTTP GET request.

        <b>Steps:</b>
        1. Check console root endpoint.
        2. Verify that HTTP response status code is 200.
        """
        step("Check get / endpoint")
        url = "http://{}.{}".format(component, config.tap_domain)
        client = HttpClientFactory.get(ServiceConfigurationProvider.get(url))
        response = client.request(method=HttpMethod.GET, path="", raw_response=True)
        assert response.status_code == HttpStatus.CODE_OK

    @pytest.mark.parametrize("component", [TAP.api_service])
    def test_api_indicator_returns_platform_header(self, component):
        """
        <b>Description:</b>
        Checks if api indicator returns platform header.

        <b>Input data:</b>
        1. Component name: api service.

        <b>Expected results:</b>
        Test passes when component api indicator HTTP response header "x-platform" contains "TAP" string.

        <b>Steps:</b>
        1. Create HTTP client.
        2. Send GET request to component api endpoint.
        3. Verify that HTTP response header "x-platform" contains "TAP" string.
        4. Verify that HTTP response text is empty.
        """
        step("Check get /api endpoint")
        url = "http://{}.{}".format(component, config.tap_domain)
        client = HttpClientFactory.get(ServiceConfigurationProvider.get(url, username=None, password=None))
        response = client.request(method=HttpMethod.GET, path="api", raw_response=True)
        step('Check if request contains "x-platform" header')
        assert response.headers['x-platform'] == 'TAP'
        assert response.text == ''

