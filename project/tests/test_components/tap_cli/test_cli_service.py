#
# Copyright (c) 2017 Intel Corporation
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
import random
import string

from modules.constants import TapMessage, TapComponent as TAP, TapEntityState, ServiceLabels
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CliService, ServiceOffering
from tests.fixtures.assertions import assert_raises_command_execution_exception, assert_not_in_with_retry, \
    assert_in_with_retry
from tap_component_config import offerings_as_parameters


logged_components = (TAP.api_service,)

# At all times at least one of the following must be available, and all that are available must not fail.
RELIABLE_OFFERINGS = [
    # ServiceLabels.GATEWAY,
    # ServiceLabels.JUPYTER,
    ServiceLabels.MOSQUITTO,
    ServiceLabels.MYSQL,
]

PARAM_ENV = [
        (["ENV1=env1", "ENV2=env2"], ['"ENV1": "env1"', '"ENV2": "env2"']),
        (["ENV=env"], ['"ENV": "env"']),
]


@pytest.mark.usefixtures("cli_login")
class TestCliService:
    INVALID_SERVICE_PLAN = "nosuchplan"
    INVALID_SERVICE_NAME = "logstashxyz"
    KAFKA_AND_HDFS_OFFERINGS = [o for o in offerings_as_parameters if o[0] == "kafka" or o[0] == "hdfs"]

    @classmethod
    @pytest.fixture(scope="class")
    def offering(cls, api_service_admin_client):
        marketplace = ServiceOffering.get_list(client=api_service_admin_client)
        usable_offerings = (o for o in marketplace if o.state == TapEntityState.READY and len(o.service_plans) > 0)
        reliable_offerings = (o for o in usable_offerings if o.label in RELIABLE_OFFERINGS)
        offering = next(reliable_offerings, None)
        assert offering is not None, "No available offerings in marketplace"
        return offering

    @classmethod
    @pytest.fixture(scope="class")
    def service(cls, context, offering, tap_cli):
        return CliService.create(context=context, offering_name=offering.label,
                                 plan_name=offering.service_plans[0].name, tap_cli=tap_cli)

    @priority.medium
    @pytest.mark.components(TAP.cli)
    @pytest.mark.bug("Cannot set multiple envs with --envs flag when creating service instance")
    @pytest.mark.parametrize("env_list, expected", PARAM_ENV)
    def test_create_service_instance_with_envs_param(self, context, offering,
                                                     tap_cli, env_list, expected):
        """
        <b>Description:</b>
        Create service with additional envs.

        <b>Input data:</b>
        1. environment variables to set

        <b>Expected results:</b>
        Created service with additional envs.

        <b>Steps:</b>
        1. Create service with additional envs
        2. Check if additional envs returned in service credentials
        """
        step("Create service with additional envs")
        svc = CliService.create(context=context, offering_name=offering.label,
                                plan_name=offering.service_plans[0].name,
                                tap_cli=tap_cli, envs=env_list)
        credentials_output = tap_cli.service_credentials(["--name", svc.name])
        assert all([result in credentials_output for result in expected])

    @pytest.mark.bugs("DPNG-14805 Cannot remove instance hdfs in plain-dir and encrypted-dir")
    @priority.high
    @pytest.mark.components(TAP.cli)
    @pytest.mark.parametrize("service_label, plan_name", KAFKA_AND_HDFS_OFFERINGS)
    def test_create_and_delete_instance_of_kafka_and_hdfs(self, context, service_label, plan_name, tap_cli):
        """
        <b>Description:</b>
        Service offerings can be divided into two groups - some of them have 'componentType' property set to value
        'instance' (e.g. kafka) and others have that value set to 'broker' (e.g. hdfs). Create service instance of both
        type, check if it's shown in service instances list and remove it.

        <b>Input data:</b>
        1. Service offering name
        2. Service plan name

        <b>Expected results:</b>
        Test passes when instance is created, displayed in service instances list and then successfully deleted.

        <b>Steps:</b>
        1. Create service instance.
        2. Verify that service instance is shown on service instances list.
        3. Delete instance.
        4. Verify that service instance is not shown on service instances list.
        """
        step("Create instance of service {}".format(service_label))
        instance = CliService.create(context=context, offering_name=service_label,
                                     plan_name=plan_name, tap_cli=tap_cli)
        step("Check that the service {} is visible on service list".format(service_label))
        instance.ensure_on_service_list()
        step("Stop service instance")
        instance.stop()
        instance.ensure_service_state(TapEntityState.STOPPED)
        step("Delete the instance of service {} and check it's no longer on the list".format(service_label))
        instance.delete()
        instance.ensure_not_on_service_list()

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_get_service_logs(self, service):
        """
        <b>Description:</b>
        Check that service logs are shown.

        <b>Input data:</b>
        1. Service instance

        <b>Expected results:</b>
        Service logs are shown with service id.

        <b>Steps:</b>
        1. Retrieve service logs
        2. Extract header line
        3. Verify that service id is present
        """
        step("Check that logs are shown for a service instance")
        logs_output = service.logs()
        header_line = logs_output.split("\n", 1)[0]
        assert "x{}".format(service.id[:8]) in header_line

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_stop_and_start_service_instance(self, service):
        """
        <b>Description:</b>
        Check that service starts & stops properly.

        <b>Input data:</b>
        1. Service instance

        <b>Expected results:</b>
        Service state changes states to stopped and running when expected.

        <b>Steps:</b>
        1. Stop service.
        2. Ensure service is stopped.
        3. Start service.
        4. Ensure service is running.
        """
        step("Stopping service ...")
        service.stop()
        step("Ensuring service is stopped ...")
        service.ensure_service_state(TapEntityState.STOPPED)
        step("Starting service ...")
        service.start()
        step("Ensuring service is stopped ...")
        service.ensure_service_state(TapEntityState.RUNNING)

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_restart_service_instance(self, service):
        """
        <b>Description:</b>
        Check that service restarts properly.

        <b>Input data:</b>
        1. Service instance

        <b>Expected results:</b>
        Service state is running.

        <b>Steps:</b>
        1. Restart service.
        2. Ensure service is starting.
        3. Ensure service is running.
        """
        step("Stopping service ...")
        service.restart()
        step("Ensuring service is running ...")
        service.ensure_service_state(TapEntityState.RUNNING)

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_cannot_delete_service_instance_in_running_state(self, service):
        """
        <b>Description:</b>
        Check that attempt to delete service in running state returns proper information.

        <b>Input data:</b>
        1. Service instance

        <b>Expected results:</b>
        Legitimate error message.

        <b>Steps:</b>
        1. Delete service.
        """
        step("Trying to delete a service")
        assert_raises_command_execution_exception(1, TapMessage.CANNOT_DELETE_RUNNING_APP,
                                                  service.delete)

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_cancel_to_delete_service_instance(self, tap_cli, service):
        """
        <b>Description:</b>
        Check deleting service with interactive mode.

        <b>Input data:</b>
        1. Service instance

        <b>Expected results:</b>
        Canceled.

        <b>Steps:</b>
        1. Canceled.
        """
        step("Cancelling service delete...")
        result = tap_cli.run_command_with_prompt(['service', 'delete', '--name', service.name],
                                                 prompt_answers=['N'])
        assert "Canceled" in result
        assert_in_with_retry(service.name, tap_cli.service_list)

    @priority.low
    @pytest.mark.components(TAP.cli)
    def test_cannot_get_logs_for_non_existing_service(self, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to retrieve logs of non existent service will return proper information.

        <b>Input data:</b>
        1. Command name: service logs show

        <b>Expected results:</b>
        Attempt to retrieve logs of non existent service will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command logs.
        2. Verify that attempt to retrieve logs of non existent service return expected message.
        """
        step("Check error when getting logs for non-existing service")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(self.INVALID_SERVICE_NAME)
        assert_raises_command_execution_exception(1, expected_msg, tap_cli.service_log, self.INVALID_SERVICE_NAME)

    @priority.low
    @pytest.mark.components(TAP.cli)
    def test_cannot_delete_non_existing_service(self, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to delete non existent service will return error.

        <b>Input data:</b>
        1. Command name: service delete

        <b>Expected results:</b>
        Attempt to delete non existent service will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command delete-service.
        2. Verify that attempt to delete non existent service return expected message.
        """
        step("Check error when deleting non-existing service")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(self.INVALID_SERVICE_NAME)
        assert_raises_command_execution_exception(1, expected_msg, tap_cli.delete_service,
                                                  ["--name", self.INVALID_SERVICE_NAME])

    @priority.low
    @pytest.mark.components(TAP.api_service, TAP.cli)
    def test_cannot_create_service_instance_with_invalid_plan(self, tap_cli, offering):
        """
        <b>Description:</b>
        Check that attempt to create service instance with invalid plan will return proper information.

        <b>Input data:</b>
        1. Command name: service create
        2. Service offering

        <b>Expected results:</b>
        Attempt to create service with invalid plan will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command create-service.
        2. Verify that attempt to create service with invalid plan return expected message.
        """
        step("Check error message when creating instance with invalid plan")
        expected_msg = TapMessage.CANNOT_FIND_PLAN_FOR_SERVICE.format(self.INVALID_SERVICE_PLAN, offering.label)
        assert_raises_command_execution_exception(1, expected_msg, tap_cli.create_service,
                                                  ["--offering", offering.label, "--plan", self.INVALID_SERVICE_PLAN,
                                                   "--name", 'test1'])

    @priority.low
    @pytest.mark.components(TAP.api_service, TAP.cli)
    def test_cannot_create_service_instance_without_instance_name(self, offering, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to create service instance without name will return proper information.

        <b>Input data:</b>
        1. Command name: service create
        2. Service offering

        <b>Expected results:</b>
        Attempt to create service without name will return proper information.

        <b>Steps:</b>
        1. Run TAP CLI with command restart.
        1. Verify that attempt to create service without name return expected message.
        """
        step("Check error message when creating instance without instance name")
        assert_raises_command_execution_exception(3, TapMessage.NOT_ENOUGH_ARGS_SERVICE,
                                                  tap_cli.create_service,
                                                  ["--offering", offering.label,
                                                   "--plan", offering.service_plans[0].name])

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_cannot_create_service_instance_with_invalid_name(self, offering, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to create service instance with invalid name will return proper information.

        <b>Input data:</b>
        1. Command name: service create
        2. Service offering

        <b>Expected results:</b>
        Attempt to create service without name will return proper information.

        <b>Steps:</b>
        1. Run TAP CLI with command.
        1. Verify that attempt to create service with invalid name returns expected message.
        """
        invalid_name = "INVALID_NAME"
        expected_message = TapMessage.NAME_HAS_INCORRECT_VALUE.format(invalid_name)
        step("Check error message when creating instance with invalid name")
        assert_raises_command_execution_exception(1, expected_message,
                                                  tap_cli.create_service,
                                                  ["--name", invalid_name,
                                                   "--offering", offering.label,
                                                   "--plan", offering.service_plans[0].name])
        assert_not_in_with_retry(invalid_name, tap_cli.service_list)


    @priority.low
    @pytest.mark.components(TAP.api_service, TAP.cli)
    def test_cannot_create_service_instance_without_plan(self, offering, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to create service instance without plan will return proper information.

        <b>Input data:</b>
        1. Command name: service create
        2. Service offering

        <b>Expected results:</b>
        Attempt to create service without plan will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command create-service.
        2. Verify that attempt to create service without plan return expected message.
        """
        step("Check error message when creating instance without plan name")
        assert_raises_command_execution_exception(3, TapMessage.NOT_ENOUGH_ARGS_SERVICE,
                                                  tap_cli.create_service, ["--offering", offering.label,
                                                                           "--name", "test"])

    @priority.low
    @pytest.mark.components(TAP.api_service, TAP.cli)
    def test_cannot_create_service_instance_without_offering(self, offering, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to create service instance without offering name will proper information.

        <b>Input data:</b>
        1. Command name: service create
        2. Service offering

        <b>Expected results:</b>
        Attempt to create service without offering name will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command create-service.
        2. Verify that attempt to create service without offering name return expected message.
        """
        step("Check error message when creating instance without offering name")
        assert_raises_command_execution_exception(3, TapMessage.NOT_ENOUGH_ARGS_SERVICE,
                                                  tap_cli.create_service, ["--plan", offering.service_plans[0].name,
                                                                           "--name", "test"])

    @priority.low
    @pytest.mark.components(TAP.cli)
    def test_cannot_create_service_instance_for_non_existing_offering(self, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to create service instance of non existing offering will return proper information.

        <b>Input data:</b>
        1. Command name: service create
        2. Non existing offering name

        <b>Expected results:</b>
        Attempt to create service instance of non existing offering will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command create-service.
        2. Verify that attempt to create service of non existing offering return expected message.
        """
        step("Check error message when creating instance for non existing offering")
        assert_raises_command_execution_exception(1, TapMessage.CANNOT_FIND_SERVICE.format(self.INVALID_SERVICE_NAME),
                                                  tap_cli.create_service, ["--offering", self.INVALID_SERVICE_NAME,
                                                                           "--plan", 'free', "--name", 'test1'])

    @priority.low
    @pytest.mark.components(TAP.cli)
    def test_get_service_instance_info(self, tap_cli, service):
        """
        <b>Description:</b>
        Check get service info.

        <b>Input data:</b>
        1. Service

        <b>Expected results:</b>
        Attempt to get info about existing service returns info.

        <b>Steps:</b>
        1. Run TAP CLI with command service info --name service-name.
        2. Verify that attempt to get existing service info returns proper info.
        """
        step("Check error message when getting non existing service info")
        result = tap_cli.get_service(service.name)
        assert (service.name, service.id) == (result["name"], result["id"])

    @priority.low
    @pytest.mark.components(TAP.cli)
    def test_cannot_get_non_existing_service_instance_info(self, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to get non existing service info returns legitimate response.

        <b>Input data:</b>
        1. Command name: service info
        2. Service name

        <b>Expected results:</b>
        Attempt to get info about non existing service returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command service info --name non-existing-service-name.
        2. Verify that attempt to get non existing service info returns legitimate response.
        """
        non_existing_name = ''.join(random.SystemRandom().
                                    choice(string.ascii_uppercase + string.digits)
                                    for _ in range(20))
        expected_message = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(non_existing_name)
        step("Check error message when getting non existing service info")
        assert_raises_command_execution_exception(1, expected_message,
                                                  tap_cli.get_service,
                                                  service_name=non_existing_name)

    @priority.low
    @pytest.mark.components(TAP.cli)
    def test_cannot_delete_service_without_providing_all_required_arguments(self, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to delete service without providing all required arguments will return proper information.

        <b>Input data:</b>
        1. Command name: service delete

        <b>Expected results:</b>
        Attempt to delete service without providing all required arguments will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command delete-service.
        2. Verify that attempt to delete service without providing all required arguments return expected message.
        """
        step("Check error message when deleting instance without instance name")
        assert_raises_command_execution_exception(3, TapMessage.NOT_ENOUGH_ARGS_SERVICE,
                                                  tap_cli.delete_service, [])

    @priority.low
    @pytest.mark.components(TAP.cli)
    def test_cannot_get_service_credentials_without_name(self, tap_cli):
        """
        <b>Description:</b>
        Check that attempt to get service credentials service without providing service name will return proper information.

        <b>Input data:</b>
        1. Command name: service credentials show

        <b>Expected results:</b>
        Attempt to get service credentials service without providing service name will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command service credentials show.
        2. Verify that attempt to get service credentials service without providing service name will return proper message.
        """
        step("Check error message when getting service credentialswithout instance name")
        assert_raises_command_execution_exception(3, TapMessage.NOT_ENOUGH_ARGS_SERVICE,
                                                  tap_cli.service_credentials, [])

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_get_service_credentials(self, tap_cli, service, offering):
        """
        <b>Description:</b>
        Check that service credentials are shown.

        <b>Input data:</b>
        1. Service instance name

        <b>Expected results:</b>
        Service credentials are shown.

        <b>Steps:</b>
        1. Retrieve service credentials
        2. Verify that offering name is present
        3. Verify that plan id is present
        """
        step("Check that logs are shown for a service instance")
        credentials_output = tap_cli.service_credentials(["--name", service.name])
        assert '-'.split(service.id)[0] in credentials_output
        assert offering.service_plans[0].id in credentials_output

    @priority.medium
    @pytest.mark.components(TAP.cli)
    def test_get_service_list(self, tap_cli):
        """
        <b>Description:</b>
        Check that service services list.

        <b>Input data:</b>
        -

        <b>Expected results:</b>
        Shown services list .

        <b>Steps:</b>
        1. Retrieve services list
        2. Verify that view headers are present
        """
        services = tap_cli.service_list()
        headers = ['SERVICE', 'PLAN', 'STATE', 'NAME', 'CREATED BY',
                   'UPDATED BY', 'UPDATE', 'MESSAGE']
        assert all(header in services for header in headers)
