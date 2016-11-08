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

from modules.constants import ApiServiceHttpStatus, ServiceLabels, ServicePlan, TapComponent as TAP
import modules.http_calls.platform.api_service as api
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceOffering
from modules.test_names import generate_test_object_name
from tests.fixtures import assertions

logged_components = (TAP.service_catalog, TAP.api_service)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.api_service)]


@incremental
class TestServiceInstantiation:

    @classmethod
    @pytest.fixture(scope="class")
    def instance(cls, class_context, api_service_admin_client):
        instance = ServiceInstance.create_with_name(context=class_context, offering_label=ServiceLabels.ETCD,
                                                    plan_name=ServicePlan.FREE, client=api_service_admin_client)
        instance.ensure_running()
        return instance

    @priority.medium
    def test_0_check_instance_on_the_list(self, instance, api_service_admin_client):
        step("Get service instances list from ApiService")
        api_service_instances_list = ServiceInstance.get_list(client=api_service_admin_client)
        step("Check if instance is on the list")
        assert instance in api_service_instances_list

    @priority.medium
    def test_1_get_instance_by_id(self, instance, api_service_admin_client):
        step("Check that service instance can be retrieved by id")
        retrieved_instance = ServiceInstance.get(service_id=instance.id, client=api_service_admin_client)
        assert instance == retrieved_instance

    @priority.medium
    def test_2_cannot_create_service_instance_with_existing_name(self, class_context, instance,
                                                                 api_service_admin_client):
        step("Try to create service instance with name that is already taken")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_CONFLICT,
                                                ApiServiceHttpStatus.MSG_SERVICE_INSTANCE_ALREADY_EXISTS
                                                .format(instance.name), ServiceInstance.create_with_name,
                                                context=class_context, offering_label=ServiceLabels.ETCD,
                                                plan_name=ServicePlan.FREE, name=instance.name,
                                                client=api_service_admin_client)

    @priority.medium
    def test_3_get_service_instance_logs(self, instance, api_service_admin_client):
        step("Check that service instance can be retrieved by id")
        retrieved_logs = instance.get_logs(client=api_service_admin_client)
        assert retrieved_logs

    @priority.medium
    def test_4_delete_service_instance(self, instance, api_service_admin_client):
        step("Delete service instance")
        instance.delete(client=api_service_admin_client)
        step("Ensure instance is not on the list")
        instance.ensure_deleted()
        assertions.assert_not_in_with_retry(instance, ServiceInstance.get_list)

    @priority.medium
    def test_5_cannot_remove_deleted_instance(self, instance, api_service_admin_client):
        step("Try delete not existing service instance")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_KEY_NOT_FOUND, instance.delete,
                                                client=api_service_admin_client)

    @priority.medium
    def test_6_cannot_retrieve_deleted_instance(self, instance, api_service_admin_client):
        step("Try retrieve service instance by providing invalid id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_CANNOT_FETCH_INSTANCE.format(instance.id),
                                                ServiceInstance.get, service_id=instance.id,
                                                client=api_service_admin_client)


class TestServiceInstantiationOther:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"

    @classmethod
    @pytest.fixture(scope="class")
    def etcd_offering(cls):
        offerings = ServiceOffering.get_list()
        etcd = next((o for o in offerings if o.label == ServiceLabels.ETCD), None)
        assert etcd is not None, "{} not found".format(ServiceLabels.ETCD)
        return etcd

    @priority.medium
    def test_cannot_retrieve_instance_with_invalid_id(self, api_service_admin_client):
        step("Try retrieve service instance by providing invalid id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_CANNOT_FETCH_INSTANCE.format(self.INVALID_ID),
                                                ServiceInstance.get, service_id=self.INVALID_ID,
                                                client=api_service_admin_client)

    @priority.medium
    def test_cannot_retrieve_logs_with_invalid_id(self, api_service_admin_client):
        step("Try to retrieve service instance logs with invalid id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, "{}", api.get_service_logs,
                                                client=api_service_admin_client, service_id=self.INVALID_ID)

    @priority.medium
    def test_cannot_remove_not_existing_service_instance(self, api_service_admin_client):
        step("Try delete not existing service instance")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_KEY_NOT_FOUND, api.delete_service,
                                                client=api_service_admin_client, service_id=self.INVALID_ID)

    @priority.medium
    def test_cannot_create_service_instance_without_name(self, etcd_offering, api_service_admin_client):
        plan_id = etcd_offering.service_plans[0].id
        step("Send create service instance request without 'name' field")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_FIELD_INCORRECT_VALUE.format("Name"),
                                                api.create_service, client=api_service_admin_client, name=None,
                                                plan_id=plan_id, offering_id=etcd_offering.id, params=None)

    @priority.medium
    def test_cannot_create_service_instance_with_invalid_plan_id(self, etcd_offering, api_service_admin_client):
        valid_name = generate_test_object_name(separator="")
        step("Send create service instance request with invalid plan_id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_PLAN_CANNOT_BE_FOUND.format(self.INVALID_ID),
                                                api.create_service, client=api_service_admin_client, name=valid_name,
                                                plan_id=self.INVALID_ID, offering_id=etcd_offering.id, params=None)

    @priority.medium
    def test_cannot_create_service_instance_with_not_allowed_characters_in_name(self, class_context,
                                                                                api_service_admin_client):
        step("Try to create service instance with not allowed characters in name")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_FIELD_INCORRECT_VALUE.format("Name"),
                                                ServiceInstance.create_with_name, context=class_context,
                                                offering_label=ServiceLabels.ETCD, plan_name=ServicePlan.FREE,
                                                name="name with space", client=api_service_admin_client)
