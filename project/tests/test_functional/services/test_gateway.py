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
from modules import test_names
from tests.fixtures import assertions

logged_components = (TAP.gateway, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.gateway, TAP.service_catalog)]


@incremental
@priority.high
class TestGateway:
    gateway_instance = None
    gateway_app = None

    def test_0_create_gateway_instance(self, class_context, test_org_user_client):
        """
        <b>Description:</b>
        Check that by creating a gateway instance the gateway application is created.

        <b>Input data:</b>
        1. user client

        <b>Expected results:</b>
        Test passes when gateway instance is successfully created.

        <b>Steps:</b>
        1. Create gateway instance with plan single.
        2. Check that gateway instance is running.
        3. Check that gateway application was created.
        """
        step("Create gateway instance")
        gateway_instance = ServiceInstance.create_with_name(
            class_context,
            name=test_names.generate_test_object_name(separator="", short=True),
            offering_label=ServiceLabels.GATEWAY,
            plan_name=ServicePlan.SINGLE,
            client=test_org_user_client
        )
        gateway_instance.ensure_running()
        validator = ApplicationStackValidator(gateway_instance)
        self.__class__.gateway_instance = gateway_instance
        self.__class__.gateway_app = validator.application

    def test_1_send_message_to_gateway_instance(self, test_org_user_client):
        """
        <b>Description:</b>
        Check that it's possible to send messages to gateway instance.

        <b>Input data:</b>
        1. gateway app

        <b>Expected results:</b>
        Test passes when message is sent to gateway instance without errors.

        <b>Steps:</b>
        1. Expose service instance url.
        2. Send message to gateway instance.
        3. Check that no error is raised.
        """
        step("Expose service instance url")
        urls = ServiceInstance.expose_urls(service_id=self.gateway_instance.id, client=test_org_user_client)
        ServiceInstance.ensure_responding(url=urls[0])
        step("Retrieve oauth token")
        http_client = HttpClientFactory.get(ServiceConfigurationProvider.get())
        token = http_client._auth._token_header
        step("Check communication with gateway instance")
        header = {"Authorization": "{}".format(token)}
        ws_url = "{}/ws".format(urls[0].replace("http", WebsocketClient.WS))
        try:
            ws = WebsocketClient(ws_url, headers=header)
            ws.send("test")
            ws.close()
        except Exception as e:
            raise AssertionError(str(e))

    def test_2_delete_gateway_instance(self, test_org_user_client):
        """
        <b>Description:</b>
        Check that gateway instance can be deleted.

        <b>Input data:</b>
        1. gateway instance

        <b>Expected results:</b>
        Test passes when gateway instance is deleted
        and doesn't appear on the instance list.

        <b>Steps:</b>
        1. Stop gateway instance.
        2. Check that gateway instance was stopped.
        3. Delete gateway instance.
        4. Check that gateway instance was deleted.
        """
        step("Stop gateway instance")
        self.gateway_instance.stop()
        self.gateway_instance.ensure_stopped()
        step("Delete gateway instance")
        self.gateway_instance.delete(client=test_org_user_client)
        self.gateway_instance.ensure_deleted()
