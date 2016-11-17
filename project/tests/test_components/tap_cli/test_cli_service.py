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

from modules.constants import TapMessage, TapComponent as TAP, TapEntityState, ServiceLabels
from modules.markers import long, priority
from modules.tap_logger import step
from modules.tap_object_model import CliOffering, CliService, ServiceOffering
from tests.fixtures.assertions import assert_raises_command_execution_exception
from tap_component_config import offerings_as_parameters


logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service, TAP.cli)]

# At all times at least one of the following must be available, and all that are available must not fail.
RELIABLE_OFFERINGS = [
    ServiceLabels.GATEWAY,
    ServiceLabels.JUPYTER,
    ServiceLabels.MOSQUITTO,
    ServiceLabels.MYSQL,
]

@pytest.mark.usefixtures("cli_login")
class TestCliService:
    INVALID_SERVICE_PLAN = "nosuchplan"
    INVALID_SERVICE_NAME = "logstashxyz"
    short = False

    @classmethod
    @pytest.fixture(scope="class")
    def offering(cls):
        marketplace = ServiceOffering.get_list()
        usable_offerings = (o for o in marketplace if o.state == TapEntityState.READY and len(o.service_plans) > 0)
        reliable_offerings = (o for o in usable_offerings if o.label in RELIABLE_OFFERINGS)
        offering = next(reliable_offerings, None)
        assert offering is not None, "No available offerings in marketplace"
        return offering

    @classmethod
    @pytest.fixture(scope="class")
    def service(cls, class_context, offering, tap_cli):
        return CliService.create(context=class_context, offering_name=offering.label,
                                 plan_name=offering.service_plans[0].name, tap_cli=tap_cli)

    @priority.high
    def test_create_and_delete_instance(self, context, offering, tap_cli):
        step("Create service instance")
        instance = CliService.create(context=context, offering_name=offering.label,
                                     plan_name=offering.service_plans[0].name, tap_cli=tap_cli)
        step("Check that the service is visible on service list")
        instance.ensure_on_service_list()
        step("Delete the instance and check it's no longer on the list")
        instance.delete()
        instance.ensure_not_on_service_list()

    @long
    @priority.low
    @pytest.mark.parametrize("service_label,plan_name", offerings_as_parameters)
    def test_create_and_delete_instance_all(self, context, service_label, plan_name, tap_cli):
        step("Create instance of service {}".format(service_label))
        instance = CliService.create(context=context, offering_name=service_label,
                                     plan_name=plan_name, tap_cli=tap_cli)
        step("Check that the service {} is visible on service list".format(service_label))
        instance.ensure_on_service_list()
        step("Delete the instance of service {} and check it's no longer on the list".format(service_label))
        instance.delete()
        instance.ensure_not_on_service_list()

    @priority.medium
    def test_get_service_logs(self, service):
        step("Check that logs are shown for a service instance")
        logs_output = service.logs()
        header_line = logs_output.split("\n", 1)[0]
        assert header_line.startswith("x{}".format(service.id[:8]))

    @priority.low
    def test_cannot_get_logs_for_non_existing_service(self, tap_cli):
        step("Check error when getting logs for non-existing service")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(self.INVALID_SERVICE_NAME)
        assert_raises_command_execution_exception(1, expected_msg, tap_cli.service_log, self.INVALID_SERVICE_NAME,
                                                  self.short)

    @priority.low
    def test_cannot_delete_non_existing_service(self, tap_cli):
        step("Check error when deleting non-existing service")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(self.INVALID_SERVICE_NAME)
        assert_raises_command_execution_exception(1, expected_msg, tap_cli.delete_service,
                                                  [self.INVALID_SERVICE_NAME], self.short)

    @priority.low
    def test_cannot_create_service_instance_with_invalid_plan(self, tap_cli, offering):
        step("Check error message when creating instance with invalid plan")
        expected_msg = TapMessage.CANNOT_FIND_PLAN_FOR_SERVICE.format(self.INVALID_SERVICE_PLAN, offering.label)
        assert_raises_command_execution_exception(1, expected_msg, tap_cli.create_service,
                                                  [offering.label, self.INVALID_SERVICE_PLAN, 'test1'], self.short)

    @priority.low
    def test_cannot_create_service_instance_without_instance_name(self, offering, tap_cli):
        step("Check error message when creating instance without instance name")
        assert_raises_command_execution_exception(1, TapMessage.NOT_ENOUGH_ARGS_CREATE_SERVICE,
                                                  tap_cli.create_service,
                                                  [offering.label, offering.service_plans[0].name], self.short)

    @priority.low
    def test_cannot_create_service_instance_without_plan(self, offering, tap_cli):
        step("Check error message when creating instance without plan name")
        assert_raises_command_execution_exception(1, TapMessage.NOT_ENOUGH_ARGS_CREATE_SERVICE,
                                                  tap_cli.create_service, [offering.label, "test"], self.short)

    @priority.low
    def test_cannot_create_service_instance_without_offering(self, offering, tap_cli):
        step("Check error message when creating instance without offering name")
        assert_raises_command_execution_exception(1, TapMessage.NOT_ENOUGH_ARGS_CREATE_SERVICE,
                                                  tap_cli.create_service, [offering.service_plans[0].name, "test"],
                                                  self.short)

    @priority.low
    def test_cannot_create_service_instance_for_non_existing_offering(self, tap_cli):
        step("Check error message when creating instance for non-existing offering")
        assert_raises_command_execution_exception(1, TapMessage.CANNOT_FIND_SERVICE.format(self.INVALID_SERVICE_NAME),
                                                  tap_cli.create_service, [self.INVALID_SERVICE_NAME, 'free', 'test1'],
                                                  self.short)

    @priority.low
    def test_cannot_delete_service_without_providing_all_required_arguments(self, tap_cli):
        step("Check error message when deleting instance without instance name")
        assert_raises_command_execution_exception(1, TapMessage.NOT_ENOUGH_ARGS_DELETE_SERVICE,
                                                  tap_cli.delete_service, [], self.short)


class TestCliServiceShortCommand(TestCliService):
    short = True
