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

import uuid

import pytest

from modules.constants import ApplicationPath, HttpStatus, TapComponent as TAP
from modules.http_calls import application_broker as broker_client
from modules.runner.tap_test_case import TapTestCase
from modules.markers import priority, components, incremental
from modules.tap_object_model import Application, ServiceInstance, ServiceType
from modules.test_names import generate_test_object_name
from tests.fixtures.test_data import TestData


logged_components = (TAP.application_broker,)
pytestmark = [components.application_broker]


class ApplicationBroker(TapTestCase):

    @priority.medium
    def test_get_catalog(self):
        self.step("Getting catalog.")
        response = broker_client.app_broker_get_catalog()
        self.assertIsNotNone(response)

    @priority.low
    def test_cannot_delete_non_existing_service(self):
        self.step("Deleting random service.")
        guid = uuid.uuid4()
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, "", broker_client.app_broker_delete_service,
                                            service_id=guid)


@incremental
@priority.medium
@pytest.mark.usefixtures("test_org", "test_space", "login_to_cf")
class ApplicationBrokerFlow(TapTestCase):

    service_name = generate_test_object_name(short=True)
    test_app = None
    cf_service = None

    def test_0_push_example_app(self):
        self.__class__.test_app = Application.push(
            space_guid=TestData.test_space.guid,
            source_directory=ApplicationPath.SAMPLE_APP
        )

    def test_1_register_service(self):
        self.step("Registering new service.")
        self.__class__.cf_service = ServiceType.app_broker_create_service_in_catalog(self.service_name,
                                                                                     "Example description",
                                                                                     self.test_app.guid)
        self.assertIsNotNone(self.cf_service)
        self.assertEqual(self.cf_service.label, self.service_name)
        response = broker_client.app_broker_get_catalog()
        services = [service['name'] for service in response["services"]]
        self.assertIn(self.service_name, services)

    def test_2_create_service_instance(self):
        self.step("Provisioning new service instance.")
        self.__class__.instance = ServiceInstance.app_broker_create_instance(
            TestData.test_org.guid,
            self.cf_service.service_plans[0]["id"],
            self.cf_service.guid,
            TestData.test_space.guid
        )

    def test_3_bind_service_instance_to_app(self):
        self.step("Binding service instance to app.")
        response = broker_client.app_broker_bind_service_instance(self.instance.guid, self.test_app.guid)
        self.assertIsNotNone(response["credentials"]["url"])

    def test_4_cannot_delete_service_with_instance(self):
        self.step("Deleting service who have existing instance.")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_INTERNAL_SERVER_ERROR, "",
                                            broker_client.app_broker_delete_service,
                                            service_id=self.cf_service.guid)
        response = broker_client.app_broker_get_catalog()
        services = [service['name'] for service in response["services"]]
        self.assertIn(self.service_name, services)

    def test_5_delete_service_instance(self):
        self.step("Deleting service instance.")
        broker_client.app_broker_delete_service_instance(self.instance.guid)

    def test_6_delete_service_offering(self):
        self.step("Delete service offering from catalog")
        broker_client.app_broker_delete_service(self.cf_service.guid)
