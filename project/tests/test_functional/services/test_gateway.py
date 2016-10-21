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
import time

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP
from modules.http_client.configuration_provider.k8s_service import ServiceConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
from modules.websocket_client import WebsocketClient
from tests.fixtures import assertions

logged_components = (TAP.gateway, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.gateway, TAP.service_catalog)]


@incremental
@priority.high
class TestGateway:
    gateway_instance = None
    gateway_app = None

    def test_0_create_gateway_instance(self, class_context, test_org_user_client):
        step("Create gateway instance")
        gateway_instance = ServiceInstance.create_with_name(
            class_context,
            offering_label=ServiceLabels.GATEWAY,
            plan_name=ServicePlan.FREE,
            client=test_org_user_client
        )
        time.sleep(20)
        validator = ApplicationStackValidator(gateway_instance)
        self.__class__.gateway_instance = gateway_instance
        self.__class__.gateway_app = validator.application

    @pytest.mark.skip("DPNG-11499 Expose no-broker specific service")
    def test_1_send_message_to_gateway_app_instance(self):
        step("Retrieve oauth token")
        http_client = HttpClientFactory.get(ServiceConfigurationProvider.get())
        token = http_client._auth._token_header
        step("Check communication with gateway app")
        header = {"Authorization": "{}".format(token)}
        ws_url = "{}://{}/ws".format(WebsocketClient.WS, self.gateway_app.urls[0])
        try:
            ws = WebsocketClient(ws_url, headers=header)
            ws.send("test")
            ws.close()
        except Exception as e:
            raise AssertionError(str(e))

    def test_2_delete_gateway_instance(self, test_org_user_client):
        step("Delete gateway instance")
        self.gateway_instance.delete(client=test_org_user_client)
        assertions.assert_not_in_with_retry(self.gateway_instance, ServiceInstance.get_list)
