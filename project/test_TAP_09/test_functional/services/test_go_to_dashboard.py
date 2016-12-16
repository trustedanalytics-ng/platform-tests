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
from modules.constants import TapComponent as TAP
from modules.http_client import HttpClientFactory, HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.markers import long, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
from modules.test_names import generate_test_object_name
from tap_component_config import offerings_as_parameters

logged_components = (TAP.service_catalog, TAP.gearpump_broker, TAP.hbase_broker,
                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                     TAP.zookeeper_wssb_broker)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.gearpump_broker, TAP.hbase_broker,
                                     TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker, TAP.zookeeper_broker,
                                     TAP.zookeeper_wssb_broker)]


class TestGoToDashboard:

    @staticmethod
    def _go_to_dashboard(instance, offering_name):
        step("Check if instance has a dashboard url")
        if instance.url is None:
            pytest.skip("{} instance doesn't have an url".format(offering_name))
        step("Go to dashboard")
        client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
        url, path = instance.url.split(config.tap_domain + "/", 1)
        try:
            client.url = url + config.tap_domain
            response = client.request(method=HttpMethod.GET, path=path, msg="Go to dashboard", raw_response=True)
            assert response.status_code // 100 == 2, "{} dashboard can't be reached".format(offering_name)
        finally:
            client.url = config.console_url

    @long
    @priority.low
    @pytest.mark.parametrize("offering_name, plan_name", offerings_as_parameters)
    def test_service_instance_dashboard(self, context, offering_name, plan_name):
        name = generate_test_object_name(separator="")
        step('Create {} service instance'.format(offering_name))
        instance = ServiceInstance.create_with_name(context, offering_label=offering_name, plan_name=plan_name,
                                                    name=name)
        instance.ensure_running()
        self._go_to_dashboard(instance, offering_name)
        step("Stop {} service instance".format(offering_name))
        instance.stop()
        instance.ensure_stopped()
        step("Delete {} service instance".format(offering_name))
        instance.delete()
