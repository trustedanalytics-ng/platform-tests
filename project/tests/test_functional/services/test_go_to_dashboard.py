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
from modules.constants import TapComponent as TAP, ParametrizedService, ServiceLabels
from modules.markers import components, long, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
from tests.fixtures.assertions import assert_no_errors
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.client_auth.http_method import HttpMethod

logged_components = (TAP.service_catalog, TAP.application_broker, TAP.gearpump_broker, TAP.hbase_broker,
                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                     TAP.zookeeper_wssb_broker)
pytestmark = [components.service_catalog, components.application_broker, components.gearpump_broker,
              components.hbase_broker, components.kafka_broker, components.smtp_broker,
              components.yarn_broker, components.zookeeper_broker, components.zookeeper_wssb_broker]


class TestGoToDashboard:

    MISSING_DASHBOARD_URL = [ServiceLabels.ATK, ServiceLabels.GATEWAY, ServiceLabels.GEARPUMP, ServiceLabels.HBASE,
                             ServiceLabels.HDFS, ServiceLabels.HIVE, ServiceLabels.ORIENT_DB_DASHBOARD,
                             ServiceLabels.SCORING_PIPELINES, ServiceLabels.YARN, ServiceLabels.ZOOKEEPER]
    DASHBOARD_URL_NOT_YET_SUPPORTED = [ServiceLabels.ELASTICSEARCH17_MULTINODE, ServiceLabels.ELK_MULTINODE,
                                       ServiceLabels.MONGO_DB_30_MULTINODE, ServiceLabels.MYSQL_MULTINODE,
                                       ServiceLabels.PSQL94_MULTINODE]

    @pytest.fixture(scope="class")
    def non_parametrized_services(self, test_marketplace):
        non_parametrized_services = []
        for service_type in test_marketplace:
            for plan in service_type.service_plans:
                if not ParametrizedService.is_parametrized(label=service_type.label, plan_name=plan["name"]):
                    non_parametrized_services.append({"label": service_type.label, "plan": plan})
        return non_parametrized_services

    @staticmethod
    def _go_to_dashboard(instance):
        assert instance.dashboard_url, "Missing dashboard url for {}".format(instance.service_label)
        client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
        url, path = instance.dashboard_url.split(config.tap_domain + "/", 1)
        try:
            client.url = url + config.tap_domain
            response = client.request(method=HttpMethod.GET, path=path, msg="Go to dashboard", raw_response=True)
            assert response.status_code // 100 == 2, "{} dashboard can't be reached".format(instance.service_label)
        finally:
            client.url = config.console_url

    def _test_service(self, org_guid, space_guid, tested_services):
        errors = []
        for service in tested_services:
            try:
                step("Create instance")
                instance = ServiceInstance.api_create(
                    org_guid=org_guid,
                    space_guid=space_guid,
                    service_label=service["label"],
                    service_plan_guid=service["plan"]["guid"]
                )
                instance.ensure_created()
                step("Go to dashboard")
                self._go_to_dashboard(instance)
                instance.api_delete()
            except Exception as e:
                errors.append("Service {} plan {}\n{}".format(service["label"], service["plan"]["name"], str(e)))
        assert_no_errors(errors)

    @long
    @priority.low
    def test_go_to_service_instance_dashboard(self, test_org, test_space, non_parametrized_services,
                                              add_admin_to_test_org, add_admin_to_test_space):
        excluded_services = self.DASHBOARD_URL_NOT_YET_SUPPORTED + self.MISSING_DASHBOARD_URL
        tested_services = [s for s in non_parametrized_services if s["label"] not in excluded_services]
        self._test_service(test_org.guid, test_space.guid, tested_services)

    @long
    @priority.low
    @pytest.mark.skip("DPNG-9173 Missing or not valid service instances dashboard urls")
    def test_instances_with_incorrect_dashboard_url(self, test_org, test_space, non_parametrized_services,
                                                    add_admin_to_test_org, add_admin_to_test_space):
        tested_service_labels = self.MISSING_DASHBOARD_URL + self.DASHBOARD_URL_NOT_YET_SUPPORTED
        tested_services = [s for s in non_parametrized_services if s["label"] in tested_service_labels]
        self._test_service(test_org.guid, test_space.guid, tested_services)
