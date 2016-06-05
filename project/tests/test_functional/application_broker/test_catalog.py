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

from modules.constants import HttpStatus, TapComponent as TAP
from modules.http_calls import application_broker as broker_client
from modules.markers import priority, components, incremental
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceType
from modules.test_names import generate_test_object_name
from tests.fixtures import assertions


logged_components = (TAP.application_broker,)
pytestmark = [components.application_broker]


class TestApplicationBrokerCatalog:

    @priority.medium
    def test_get_catalog(self):
        step("Getting catalog.")
        response = broker_client.app_broker_get_catalog()
        assert response is not None

    @priority.low
    def test_cannot_delete_non_existing_service(self):
        step("Deleting random service.")
        guid = uuid.uuid4()
        assertions.assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, "", broker_client.app_broker_delete_service,
                                                service_id=guid)


@incremental
@priority.medium
class TestApplicationBrokerFlow:

    service_name = generate_test_object_name(short=True)
    cf_service = None

    def test_1_register_service(self, sample_python_app):
        step("Registering new service.")
        self.__class__.cf_service = ServiceType.app_broker_create_service_in_catalog(self.service_name,
                                                                                     "Example description",
                                                                                     sample_python_app.guid)
        assert self.cf_service is not None
        assert self.cf_service.label == self.service_name
        response = broker_client.app_broker_get_catalog()
        services = [service['name'] for service in response["services"]]
        assert self.service_name in services

    def test_2_create_service_instance(self, test_org, test_space):
        step("Provisioning new service instance.")
        self.__class__.instance = ServiceInstance.app_broker_create_instance(
            test_org.guid,
            self.cf_service.service_plans[0]["id"],
            self.cf_service.guid,
            test_space.guid
        )

    def test_3_bind_service_instance_to_app(self, sample_python_app):
        step("Binding service instance to app.")
        response = broker_client.app_broker_bind_service_instance(self.instance.guid, sample_python_app.guid)
        assert response["credentials"]["url"] is not None

    def test_4_cannot_delete_service_with_instance(self):
        step("Deleting service which has existing instance.")
        assertions.assert_raises_http_exception(HttpStatus.CODE_INTERNAL_SERVER_ERROR, "",
                                                broker_client.app_broker_delete_service,
                                                service_id=self.cf_service.guid)
        response = broker_client.app_broker_get_catalog()
        services = [service['name'] for service in response["services"]]
        assert self.service_name in services

    def test_5_delete_service_instance(self):
        step("Deleting service instance.")
        broker_client.app_broker_delete_service_instance(self.instance.guid)

    def test_6_delete_service_offering(self):
        step("Delete service offering from catalog")
        broker_client.app_broker_delete_service(self.cf_service.guid)
