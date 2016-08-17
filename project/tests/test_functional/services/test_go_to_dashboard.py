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
from modules.constants import TapComponent as TAP, ParametrizedService
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.markers import long, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceType
from modules.tap_object_model.flows.services import create_instance, delete_instance
from tests.fixtures.assertions import assert_no_errors

logged_components = (TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker,
                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                     TAP.zookeeper_wssb_broker)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker,
                                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                                     TAP.zookeeper_wssb_broker)]


class TestGoToDashboard:

    @pytest.fixture(scope="class")
    def global_offerings(self, test_marketplace):
        return [s for s in test_marketplace if ServiceType.TEST_SERVICE_PREFIX not in s.label]

    @pytest.fixture(scope="class")
    def non_parametrized_services(self, global_offerings):
        non_parametrized_services = []
        for service_type in global_offerings:
            for plan in service_type.service_plans:
                if not ParametrizedService.is_parametrized(label=service_type.label, plan_name=plan["name"]):
                    non_parametrized_services.append({"label": service_type.label, "plan": plan})
        return non_parametrized_services

    @staticmethod
    def _go_to_dashboard(instance):
        step("Check if instance has a dashboard url")
        if instance.dashboard_url:
            step("Go to dashboard")
            client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
            url, path = instance.dashboard_url.split(config.tap_domain + "/", 1)
            try:
                client.url = url + config.tap_domain
                response = client.request(method=HttpMethod.GET, path=path, msg="Go to dashboard", raw_response=True)
                assert response.status_code // 100 == 2, "{} dashboard can't be reached".format(instance.service_label)
            finally:
                client.url = config.console_url

    @long
    @priority.low
    def test_service_instance_dashboard(self, context, test_org, test_space, non_parametrized_services,
                                        add_admin_to_test_org, add_admin_to_test_space):
        errors = []
        for service in non_parametrized_services:
            try:
                instance = create_instance(context=context, org_guid=test_org.guid, space_guid=test_space.guid,
                                           service_label=service["label"], plan_guid=service["plan"]["guid"])
                self._go_to_dashboard(instance)
                delete_instance(instance, test_space.guid)
            except Exception as e:
                errors.append("Service {} plan {}\n{}".format(service["label"], service["plan"]["name"], str(e)))
        assert_no_errors(errors)
