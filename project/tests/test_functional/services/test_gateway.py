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

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP
from modules.http_client.configuration_provider.cloud_foundry import CloudFoundryConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, incremental, priority
from modules.tap_object_model import ServiceInstance, User
from tests.fixtures.test_data import TestData
from modules.websocket_client import WebsocketClient

logged_components = (TAP.gateway, TAP.application_broker, TAP.service_catalog)
pytestmark = [components.gateway, components.application_broker, components.service_catalog]


@incremental
@priority.high
class Gateway(TapTestCase):
    gateway_instance = None
    kafka_instance = None
    gateway_app = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def space_developer_user(cls, test_org, test_space, class_context):
        cls.step("Create space developer client")
        space_developer_user = User.api_create_by_adding_to_space(class_context, test_org.guid, test_space.guid,
                                                                  roles=User.SPACE_ROLES["developer"])
        cls.space_developer_client = space_developer_user.login()

    def test_0_create_gateway_instance(self, class_context):
        self.step("Create gateway instance")
        gateway_instance = ServiceInstance.api_create_with_plan_name(
            class_context,
            TestData.test_org.guid,
            TestData.test_space.guid,
            ServiceLabels.GATEWAY,
            service_plan_name=ServicePlan.SIMPLE_ATK,
            client=self.space_developer_client
        )
        validator = ApplicationStackValidator(gateway_instance)
        validator.validate(expected_bindings=[ServiceLabels.KAFKA])
        self.__class__.gateway_instance = gateway_instance
        self.__class__.gateway_app = validator.application
        self.__class__.kafka_instance = validator.application_bindings[ServiceLabels.KAFKA]

    def test_1_send_message_to_gateway_app_instance(self):
        self.step("Retrieve oauth token")
        http_client = HttpClientFactory.get(CloudFoundryConfigurationProvider.get())
        token = http_client._auth._token
        self.step("Check communication with gateway app")
        header = {"Authorization": "Bearer{}".format(token)}
        ws_url = "{}://{}/ws".format(WebsocketClient.WS, self.gateway_app.urls[0])
        try:
            ws = WebsocketClient(ws_url, headers=header)
            ws.send("test")
            ws.close()
        except Exception as e:
            raise AssertionError(str(e))

    def test_2_delete_gateway_instance(self):
        self.step("Delete gateway instance")
        self.gateway_instance.api_delete(client=self.space_developer_client)
        self.assertNotInWithRetry(self.gateway_instance, ServiceInstance.api_get_list, TestData.test_space.guid)
        self.step("Check that bound kafka instance was also deleted")
        service_instances = ServiceInstance.api_get_list(TestData.test_space.guid)
        self.assertNotIn(self.kafka_instance, service_instances, "Kafka instance was not deleted")
