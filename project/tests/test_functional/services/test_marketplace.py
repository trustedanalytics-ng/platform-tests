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

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, ApiServiceHttpStatus, ServiceLabels, ServicePlan, \
    TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.markers import long, priority
from modules.service_tools.jupyter import Jupyter
from modules.tap_logger import step
from modules.tap_object_model import KubernetesPod, ServiceInstance
from tap_component_config import offerings, filtered_offerings, PlanKeys
from tests.fixtures.assertions import assert_raises_http_exception, assert_in_with_retry, \
    assert_unordered_list_equal


logged_components = (TAP.service_catalog, TAP.gearpump_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker,
                     TAP.zookeeper_broker, TAP.zookeeper_wssb_broker)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.gearpump_broker, TAP.kafka_broker, TAP.smtp_broker,
                                     TAP.yarn_broker, TAP.zookeeper_broker, TAP.zookeeper_wssb_broker)]


class TestMarketplaceServices:

    def _create_jupyter_instance_and_login(self, context, param_key, param_value):
        param = {param_key: param_value}
        step("Create service instance and check it exist in list")
        jupyter = Jupyter(context, params=param)
        assert_in_with_retry(jupyter.instance, ServiceInstance.get_list)
        step("Get credentials for the new jupyter service instance")
        jupyter.get_credentials()
        jupyter.login()
        terminal = jupyter.connect_to_terminal(terminal_no=0)
        _ = terminal.get_output()
        return terminal

    @pytest.fixture(scope="class")
    def service_instance(self, class_context):
        step("Create service instance")
        instance = ServiceInstance.create_with_name(
            context=class_context,
            offering_label=ServiceLabels.RABBIT_MQ,
            plan_name=ServicePlan.SINGLE_SMALL,
        )
        step("Ensure that instance is running")
        instance.ensure_running()
        return instance

    def parse_storage_output(self, output):
        parsed_output = {}
        if "Warning" in output[0]:
            output = output[1:]
        headers = output[0].split(maxsplit=5)
        for line in output[1:-1]:
            parsed_output.update({line.split()[0]: {headers[i]: line.split()[i] for i in range(1, len(headers))}})
        return parsed_output

    def _get_instance_pod(self, instance):
        step("Find pod for instance '{}'".format(instance.name))
        pod_list = KubernetesPod.get_list()
        instance_pod = next((pod for pod in pod_list if pod.instance_id_label == instance.id), None)
        return instance_pod

    def _validate_memory(self, instance_pod, expected_resources):
        step("Check memory limit.")
        memory = instance_pod.containers[0]["resources"]["limits"][PlanKeys.MEMORY]
        assert memory == expected_resources[PlanKeys.MEMORY]

    def _validate_compute_nodes(self, instance_pod, expected_resources):
        step("Check compute nodes number")
        if PlanKeys.NODES in expected_resources.keys():
            assert len(instance_pod.nodes) == expected_resources[PlanKeys.NODES]

    def compare_storage(self, storage, expected_storage):
        storage_float = float(storage[:-1])
        expected_storage_float = float(expected_storage[:-1])
        assert expected_storage_float - storage_float < 2

    def _validate_storage(self, instance_pod, tunnel, offering_name, expected_resources):
        command = ["kubectl", "exec", instance_pod.name, "df", "--", "-h"]
        output = tunnel._jump_client.ssh(["ssh", "-tt", "compute-master"] + command)
        parsed_output = self.parse_storage_output(output)
        entry = next((v for k, v in parsed_output.items() if "/rbd" in k), None)
        if expected_resources[PlanKeys.STORAGE]:
            assert entry, "Storage was not allocated for {}".format(offering_name)
            self.compare_storage(entry["Size"], expected_resources[PlanKeys.STORAGE])
        else:
            assert entry is expected_resources[PlanKeys.STORAGE], \
                "Storage for offering {} was allocated, but it shouldn't.".format(offering_name)

    def validate_resources(self, instance, offering_label, plan_name, tunnel):
        expected_resources = offerings[offering_label][plan_name]
        if all(x in expected_resources.keys() for x in [PlanKeys.NODES, PlanKeys.MEMORY, PlanKeys.STORAGE]):
            instance_pod = self._get_instance_pod(instance)
            assert instance_pod is not None, "Pod for instance '{}' was not found".format(instance.name)
            self._validate_memory(instance_pod, expected_resources)
            self._validate_compute_nodes(instance_pod, expected_resources)
            self._validate_storage(instance_pod, tunnel, offering_label, expected_resources)
        else:
            step("Plan {} of offering {} does not have expected resource information".format(plan_name, offering_label))

    @pytest.mark.bugs("DPNG-15227 elasticsearch24 - cannot see assigned storage")
    @long
    @priority.high
    @pytest.mark.usefixtures("open_tunnel")
    @pytest.mark.parametrize("role", ["user"])
    @pytest.mark.parametrize("offering_name, plan_name", filtered_offerings)
    def test_create_and_delete_service_instance(self, context, test_user_clients, role, offering_name, plan_name,
                                                open_tunnel):
        """
        <b>Description:</b>
        Check service instance creation and deletion.

        <b>Input data:</b>
        1. non parametized marketplace services

        <b>Expected results:</b>
        Test passes when service instance is created and deleted successfully.

        <b>Steps:</b>
        1. Create service instance.
        2. Ensure that instance is running.
        3. Check that service instance is present on instances list.
        4. Stop service instance.
        5. Delete service instance.
        """
        client = test_user_clients[role]
        step("Create an instance")
        instance = ServiceInstance.create_with_name(context, offering_label=offering_name, plan_name=plan_name,
                                                    client=client)
        step("Ensure that instance is running")
        instance.ensure_running()
        step("Check that service instance is present")
        assert_in_with_retry(instance, ServiceInstance.get_list, name=instance.name)
        step("Validate resources")
        self.validate_resources(instance, offering_name, plan_name, open_tunnel)
        step("Stop service instance")
        instance.stop()
        instance.ensure_stopped()
        step("Delete an instance")
        instance.delete()
        instance.ensure_deleted()

    @pytest.mark.skip(reason="DPNG-10885 credentials endpoint is not implemented yet")
    @priority.low
    def test_create_instance_with_non_required_parameter_and_check_credentials(self, context):
        """
        <b>Description:</b>
        Check that if service instance can be created with additional parameters.

        <b>Input data:</b>
        1. Jupyter offering

        <b>Expected results:</b>
        Test passes when service is created and passed parameters
        can be viewed in jupyter terminal output.

        <b>Steps:</b>
        1. Create jupyter service instance with additional parameters.
        2. Run 'env' command in jupyter terminal.
        3. Check that output contains passed parameters.
        """
        param_key = "test_param"
        param_value = "test_value"
        step("Create service instance with additional params")
        terminal = self._create_jupyter_instance_and_login(context, param_key, param_value)
        terminal.send_input("env\n")
        output = "".join(terminal.get_output())
        step("Verify if additionals params are returned in credentials")
        assert "{}={}".format(param_key, param_value) in output

    @priority.medium
    def test_cannot_create_service_instance_with_name_of_an_existing_instance(self, context):
        """
        <b>Description:</b>
        Check that it's impossible to create a service instance
        with name that is already used by another instance.

        <b>Input data:</b>
        1. Rabbit mq offering
        2. Redis offering

        <b>Expected results:</b>
        Test passes if platform returns 409 http code.

        <b>Steps:</b>
        1. Create rabbit mq service instance.
        2. Check that instance is running.
        3. Try to create redis service insance with same name as rabbit mq instance.
        4. Check that platform returns 409 http code.
        """
        step("Create service instance")
        instance = ServiceInstance.create_with_name(context, offering_label=ServiceLabels.RABBIT_MQ,
                                                    plan_name=ServicePlan.SINGLE_SMALL)
        step("Ensure that instance is running")
        instance.ensure_running()
        step("Try to create service instance with already taken name")
        with pytest.raises(UnexpectedResponseError) as e:
            ServiceInstance.create_with_name(context, offering_label=ServiceLabels.REDIS,
                                             plan_name=ServicePlan.SINGLE_SMALL, name=instance.name)
        assert e.value.status == HttpStatus.CODE_CONFLICT, "Created service instance with already taken name"

    @priority.low
    def test_cannot_create_instance_without_a_name(self, context):
        """
        <b>Description:</b>
        Check that it's impossible to create a service instance without a name.

        <b>Input data:</b>
        1. Rabbit mq offering

        <b>Expected results:</b>
        Test passes if platform returns 402 http code.

        <b>Steps:</b>
        1. Get current service instance list.
        2. Try to create a rabbit mq service instance without a name.
        3. Check that platform returns 402 http status code.
        4. Check that no new service instances were created.
        """
        expected_instance_list = ServiceInstance.get_list()
        step("Check that instance cannot be created with empty name")
        expected_msg = ApiServiceHttpStatus.MSG_FIELD_ZERO_VALUE.format("Name")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, expected_msg,
                                     ServiceInstance.create_with_name, context=context,
                                     offering_label=ServiceLabels.RABBIT_MQ, plan_name=ServicePlan.SINGLE_SMALL,
                                     name="")
        assert_unordered_list_equal(expected_instance_list, ServiceInstance.get_list(), "New instance was created")
