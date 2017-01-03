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

logged_components = (TAP.api_service, )
pytestmark = [pytest.mark.components(TAP.api_service)]


@incremental
class TestServiceInstantiation:

    @classmethod
    @pytest.fixture(scope="class")
    def instance(cls, class_context, api_service_admin_client):
        instance = ServiceInstance.create_with_name(context=class_context, offering_label=ServiceLabels.KAFKA,
                                                    plan_name=ServicePlan.SHARED, client=api_service_admin_client)
        instance.ensure_running(client=api_service_admin_client)
        return instance

    @priority.medium
    def test_0_check_instance_on_the_list(self, instance, api_service_admin_client):
        """
        <b>Description:</b>
        Verify the service instance is on the list

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        Instance is on the list

        <b>Steps:</b>
        - Retrieve the list of instances
        - Verify the instance is on the list
        """
        step("Get service instances list from ApiService")
        api_service_instances_list = ServiceInstance.get_list(client=api_service_admin_client)
        step("Check if instance is on the list")
        assert instance in api_service_instances_list

    @priority.medium
    def test_1_get_instance_by_id(self, instance, api_service_admin_client):
        """
        <b>Description:</b>
        Retrieve the instance by id

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        It's possible to retrieve service instance by id

        <b>Steps:</b>
        - Retrieve the service instance by id
        - Verify it's the same instance as created before
        """
        step("Check that service instance can be retrieved by id")
        retrieved_instance = ServiceInstance.get(service_id=instance.id, client=api_service_admin_client)
        assert instance == retrieved_instance

    @priority.medium
    def test_2_cannot_create_service_instance_with_existing_name(self, class_context, instance,
                                                                 api_service_admin_client):
        """
        <b>Description:</b>
        Check if it's possible to create instance with the same name twice

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to create two instances with the same name

        <b>Steps:</b>
        - Create another service instance with the same name
        """
        step("Try to create service instance with name that is already taken")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_CONFLICT,
                                                ApiServiceHttpStatus.MSG_SERVICE_INSTANCE_ALREADY_EXISTS
                                                .format(instance.name), ServiceInstance.create_with_name,
                                                context=class_context, offering_label=ServiceLabels.KAFKA,
                                                plan_name=ServicePlan.SHARED, name=instance.name,
                                                client=api_service_admin_client)

    @priority.medium
    def test_3_get_service_instance_logs(self, instance, api_service_admin_client):
        """
        <b>Description:</b>
        Retrieve the logs from the service instance

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        It's possible to retrieve logs from the service instance

        <b>Steps:</b>
        - Retrieve the service instance logs
        """
        step("Check that service instance logs can be retrieved")
        retrieved_logs = instance.get_logs(client=api_service_admin_client)
        assert retrieved_logs

    @priority.medium
    def test_4_stop_start_restart_service(self, instance, api_service_admin_client):
        """
        <b>Description:</b>
        Stop and start and restart service instance

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        It' possible to stop and start and restart service instance

        <b>Steps:</b>
        - Stop the service instance and verify it has stopped
        - Start the service instance and verify it's running
        - Restart the service instance and verify it's running
        """
        step("Stop the service instance")
        instance.stop(client=api_service_admin_client)
        step("Make sure the service instance is stopped")
        instance.ensure_stopped(client=api_service_admin_client)

        step("Start the service instance")
        instance.start(client=api_service_admin_client)
        step("Make sure the service instance is running")
        instance.ensure_running(client=api_service_admin_client)

        step("Restart the service instance")
        instance.restart(client=api_service_admin_client)
        step("Make sure the service instance is running")
        instance.ensure_running(client=api_service_admin_client)

    @priority.medium
    def test_5_delete_service_instance(self, instance, api_service_admin_client):
        """
        <b>Description:</b>
        Deletes the service instance

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        - It's possible to delete service instance
        - Service instance no longer exists

        <b>Steps:</b>
        - Stop the service instance and make sure it has stopped
        - Delete the service instance and make sure it was removed
        """
        step("Stop service instance")
        instance.stop(client=api_service_admin_client)
        instance.ensure_stopped(client=api_service_admin_client)
        step("Delete service instance")
        instance.delete(client=api_service_admin_client)
        step("Ensure instance is not on the list")
        instance.ensure_deleted()
        assertions.assert_not_in_with_retry(instance, ServiceInstance.get_list)

    @priority.medium
    def test_6_cannot_remove_deleted_instance(self, instance, api_service_admin_client):
        """
        <b>Description:</b>
        Try to remove deleted service instance

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to remove an instance that was removed

        <b>Steps:</b>
        - Remove the service instance again
        """
        step("Try delete not existing service instance")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_KEY_NOT_FOUND, instance.delete,
                                                client=api_service_admin_client)

    @priority.medium
    def test_7_cannot_retrieve_deleted_instance(self, instance, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to retrieve deleted service instance

        <b>Input data:</b>
        - service instance
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to retrieve removed service instance

        <b>Steps:</b>
        - Try to retrieve service instance by id
        """
        step("Try retrieve service instance that was removed")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_CANNOT_FETCH_INSTANCE.format(instance.id),
                                                ServiceInstance.get, service_id=instance.id,
                                                client=api_service_admin_client)


class TestServiceInstantiationOther:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"

    @classmethod
    @pytest.fixture(scope="class")
    def etcd_offering(cls, api_service_admin_client):
        offerings = ServiceOffering.get_list(client=api_service_admin_client)
        offering = next((o for o in offerings if o.label == ServiceLabels.KAFKA), None)
        assert offering is not None, "{} not found".format(ServiceLabels.KAFKA)
        return offering

    @classmethod
    @pytest.fixture(scope="class")
    def invalid_instance(cls, api_service_admin_client):
        """Creates a servicve instance with invalid id"""
        return ServiceInstance(service_id=TestServiceInstantiationOther.INVALID_ID,
                               name=None, offering_id=None, plan_id=None,
                               bindings=None, state=None, offering_label=None,
                               client=api_service_admin_client)

    @priority.medium
    def test_cannot_retrieve_instance_with_invalid_id(self, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to retrieve service instance by providing invalid id

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to retrieve any instance by providing invalid id

        <b>Steps:</b>
        - Try to retrieve instance by providing bad id
        """
        step("Try retrieve service instance by providing invalid id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_CANNOT_FETCH_INSTANCE.format(self.INVALID_ID),
                                                ServiceInstance.get, service_id=self.INVALID_ID,
                                                client=api_service_admin_client)

    @priority.medium
    def test_cannot_stop_service_with_invalid_id(self, invalid_instance):
        """
        <b>Description:</b>
        Stop non-existent service instance

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to stop non-existent service instance

        <b>Steps:</b>
        Stop the non-existent service instance
        """
        step("Stop the non existent service instance")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_KEY_NOT_FOUND,
                                                invalid_instance.stop)

    @priority.medium
    def test_cannot_start_service_with_invalid_id(self, invalid_instance):
        """
        <b>Description:</b>
        Start non-existent service instance

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to start non-existent service instance

        <b>Steps:</b>
        Start the non-existent service instance
        """
        step("Start the non existent service instance")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_KEY_NOT_FOUND,
                                                invalid_instance.start)

    @priority.medium
    def test_cannot_restart_service_with_invalid_id(self, invalid_instance):
        """
        <b>Description:</b>
        Restart non-existent service instance

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to restart non-existent service instance

        <b>Steps:</b>
        Restart the non-existent service instance
        """
        step("Restart the non existent service instance")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_KEY_NOT_FOUND,
                                                invalid_instance.restart)

    @priority.medium
    def test_cannot_retrieve_logs_with_invalid_id(self, api_service_admin_client):
        """
        <b>Description:</b>
        Retrieve logs from non-existent service instance

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to retrieve any logs

        <b>Steps:</b>
        Retrieve the logs from non-existing service instance
        """
        step("Try to retrieve service instance logs with invalid id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, "{}", api.get_service_logs,
                                                client=api_service_admin_client, service_id=self.INVALID_ID)

    @priority.medium
    def test_cannot_remove_not_existing_service_instance(self, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to remove non-existent service instance

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to remove service instance that does not exist

        <b>Steps:</b>
        Remove non-existing service instance
        """
        step("Try delete not existing service instance")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_KEY_NOT_FOUND, api.delete_service,
                                                client=api_service_admin_client, service_id=self.INVALID_ID)

    @priority.medium
    def test_cannot_create_service_instance_without_name(self, etcd_offering, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to create service instance without a name

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to create service instance without a name

        <b>Steps:</b>
        Create the service instance and don't provide a name
        """
        plan_id = etcd_offering.service_plans[0].id
        step("Send create service instance request without 'name' field")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_FIELD_INCORRECT_VALUE.format("Name"),
                                                api.create_service, client=api_service_admin_client, name=None,
                                                plan_id=plan_id, offering_id=etcd_offering.id, params=None)

    @priority.medium
    @pytest.mark.bugs("DPNG-14049 Adjust expected response message for test_cannot_create_service_instance_with_invalid_plan_id")
    def test_cannot_create_service_instance_with_invalid_plan_id(self, etcd_offering, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to create service instance with invalid plan id

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to create service with invalid plan id

        <b>Steps:</b>
        Create a service instance with invalid plan id
        """
        valid_name = generate_test_object_name(separator="")
        step("Send create service instance request with invalid plan_id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_PLAN_CANNOT_BE_FOUND.format(self.INVALID_ID),
                                                api.create_service, client=api_service_admin_client, name=valid_name,
                                                plan_id=self.INVALID_ID, offering_id=etcd_offering.id, params=None)

    @priority.medium
    def test_cannot_create_service_instance_with_not_allowed_characters_in_name(self, class_context,
                                                                                api_service_admin_client):
        """
        <b>Description:</b>
        Create a service instance with bad characters in name

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to create service instance with bad name

        <b>Steps:</b>
        Give service instance a bad name
        """
        step("Try to create service instance with not allowed characters in name")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_FIELD_INCORRECT_VALUE.format("Name"),
                                                ServiceInstance.create_with_name, context=class_context,
                                                offering_label=ServiceLabels.KAFKA, plan_name=ServicePlan.SHARED,
                                                name="name with space", client=api_service_admin_client)
