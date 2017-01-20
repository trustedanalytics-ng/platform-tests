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

from modules.constants import TapMessage, TapComponent as TAP
from modules.constants import TapEntityState
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_cli import TapCli
from modules.tap_object_model import CliService, CliOffering, CliBinding
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_command_execution_exception


pytestmark = [pytest.mark.components(TAP.cli)]


@pytest.fixture(scope="module")
def offering(session_context, tap_cli, cli_login):
    return CliOffering.create(context=session_context, tap_cli=tap_cli)


@pytest.mark.usefixtures("cli_login")
class TestCliBinding:

    @pytest.fixture(scope="class")
    def service_instance_1(self, class_context, tap_cli, offering):
        return CliService.create(
            context=class_context,
            offering_name=offering.name,
            plan_name=offering.plans[0].name,
            tap_cli=tap_cli)

    @pytest.fixture(scope="class")
    def service_instance_2(self, class_context, tap_cli, offering):
        return CliService.create(
            context=class_context,
            offering_name=offering.name,
            plan_name=offering.plans[0].name,
            tap_cli=tap_cli)

    @pytest.fixture(scope="class")
    def nonexistent_service(self, tap_cli, offering):
        return CliService(
            name=generate_test_object_name(separator="-"),
            offering_name=offering.name,
            plan_name=offering.plans[0].name,
            tap_cli=tap_cli)

    @priority.high
    def test_bind_and_unbind_services_with_dst_param(self, tap_cli, class_context, service_instance_1, service_instance_2):
        """
        <b>Description:</b>
        Check that service instance can be bind to other service instance.

        <b>Input data:</b>
        1. Service instance to bind to
        2. Second service instance that will be bind

        <b>Expected results:</b>
        Service instances are successfully bind and than successfully unbind.

        <b>Steps:</b>
        1. Bind second service to first one.
        2. Check that second service is on first service binding list
        3. Unbind second service from first.
        4. Check that second service is not shown on first service binding list
        """
        step("Bind one service instance to another")
        binding = CliBinding.create(tap_cli=tap_cli, context=class_context, type=TapCli.SERVICE,
                                    name=service_instance_2.name, dst_name=service_instance_1.name)
        step("Check that the services are bound")
        binding.ensure_on_bindings_list()
        service_instance_1.ensure_service_state(TapEntityState.RUNNING)
        step("Unbind service instance")
        binding.delete()
        step("Check that the services are not bound")
        binding.ensure_not_on_bindings_list()
        service_instance_1.ensure_service_state(TapEntityState.RUNNING)

    @priority.medium
    def test_bind_and_unbind_applications_with_src_param(self, tap_cli, class_context, sample_python_app, sample_java_app):
        """
        <b>Description:</b>
        Check that application can be bound to other application (src flow).

        <b>Input data:</b>
        1. Application to bind to
        2. Second application instance that will be bound

        <b>Expected results:</b>
        Applications are successfully bound and then successfully unbound.

        <b>Steps:</b>
        1. Bind java app to python app (java app is source in this binding)
        2. Check that java app is on python app's binding list
        3. Unbind java app from python app.
        4. Check that java app is missing on python app's binding list
        """
        binding = CliBinding.create(context=class_context, type=TapCli.APPLICATION, tap_cli=tap_cli,
                          name=sample_python_app.name, src_name=sample_java_app.name)
        binding.ensure_on_bindings_list()
        sample_python_app.ensure_running()
        binding.delete()
        binding.ensure_not_on_bindings_list()
        sample_python_app.ensure_running()

    @priority.medium
    def test_bind_and_unbind_applications_with_dst_param(self, tap_cli, class_context, sample_python_app, sample_java_app):
        """
        <b>Description:</b>
        Check that application can be bound to other application (dst flow).

        <b>Input data:</b>
        1. Application to bind to
        2. Second application instance that will be bound

        <b>Expected results:</b>
        Applications are successfully bound and then successfully unbound.

        <b>Steps:</b>
        1. Bind python app to java app (java app is destination in this binding)
        2. Check that python app is on java app's binding list
        3. Unbind python app from java app.
        4. Check that python app is missing on java app's binding list
        """
        binding = CliBinding.create(context=class_context, type=TapCli.APPLICATION, tap_cli=tap_cli,
                                    name=sample_python_app.name, dst_name=sample_java_app.name)
        binding.ensure_on_bindings_list()
        sample_java_app.ensure_running()
        binding.delete()
        binding.ensure_not_on_bindings_list()
        sample_java_app.ensure_running()

    @priority.low
    def test_cannot_bind_invalid_service(self, context, tap_cli, service_instance_1, nonexistent_service):
        """
        <b>Description:</b>
        Check that attempt to bind non existent service instance will return proper information.

        <b>Input data:</b>
        1. Service instance to bind to
        2. Non existent service instance to bind

        <b>Expected results:</b>
        Attempt to bind non existent instances will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command bind.
        2. Verify that attempt to bind non existent service instance return expected message.
        """
        step("Check that attempt to bind invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        assert_raises_command_execution_exception(1, expected_msg, CliBinding.create,
                      context=context, tap_cli=tap_cli, type=TapCli.SERVICE,
                      name=nonexistent_service.name, dst_name=service_instance_1.name)

    @priority.low
    def test_cannot_bind_service_to_invalid_service(self, context, tap_cli, service_instance_1, nonexistent_service):
        """
        <b>Description:</b>
        Check that attempt to bind to non existent service instance will return proper information.

        <b>Input data:</b>
        1. Non existent service instance to bind to
        2. Service instance to bind

        <b>Expected results:</b>
        Attempt to bind non existent instances will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command bind.
        2. Verify that attempt bind to non existent service instance return expected message.
        """
        step("Check that attempt to bind to invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        assert_raises_command_execution_exception(1, expected_msg, CliBinding.create,
                                                  context=context, tap_cli=tap_cli, type=TapCli.SERVICE,
                                                  name=service_instance_1.name, dst_name=nonexistent_service.name)

    @priority.low
    def test_cannot_unbind_invalid_service(self, tap_cli, service_instance_1, nonexistent_service):
        """
        <b>Description:</b>
        Check that attempt to unbind non existent service instance will return proper information.

        <b>Input data:</b>
        1. Service instance to unbind from
        2. Non existent service instance to unbind

        <b>Expected results:</b>
        Attempt to unbind non existent instances will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command unbind.
        2. Verify that attempt unbind non existent service instance return expected message
        """
        step("Check that attempt to unbind invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        binding = CliBinding(tap_cli=tap_cli, type=TapCli.SERVICE,
                             name=nonexistent_service.name, dst_name=service_instance_1.name)
        assert_raises_command_execution_exception(1, expected_msg, binding.delete)


    @priority.low
    def test_cannot_unbind_service_from_invalid_service(self, tap_cli, service_instance_1, nonexistent_service):
        """
        <b>Description:</b>
        Check that attempt to unbind non existent service instance will return proper information.

        <b>Input data:</b>
        1. Non existent service instance to unbind from
        2. Service instance to unbind

        <b>Expected results:</b>
        Attempt to unbind non existent instances will return proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command unbind.
        2. Verify that attempt unbind from non existent service instance return expected message.
        """
        step("Check that attempt to unbind from invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        binding = CliBinding(tap_cli=tap_cli, type=TapCli.SERVICE,
                             name=service_instance_1.name, dst_name=nonexistent_service.name)
        assert_raises_command_execution_exception(1, expected_msg, binding.delete)

    @priority.low
    def test_cannot_delete_bound_service(self, class_context, tap_cli, service_instance_1, service_instance_2):
        """
        <b>Description:</b>
        Check that an attempt to delete bound service instance fails with an error and instance won't be removed.

        <b>Input data:</b>
        1. Service instance to unbind from
        2. Service instance to unbind

        <b>Expected results:</b>
        Attempt to delete bounded instance will return proper message and not delete service.

        <b>Steps:</b>
        1. Bind second service to first one.
        2. Check that second service is on first service binding list.
        3. Verify that attempt to delete bounded service instance return expected message.
        4. Check that second service is shown on services list.
        5. Check that second service is shown on first service binding list
        """
        step("Bind service instances")

        binding = CliBinding.create(context=class_context, type=TapCli.SERVICE, tap_cli=tap_cli,
                                    name=service_instance_2.name, dst_name=service_instance_1.name)
        binding.ensure_on_bindings_list()
        step("Check that an attempt to delete bound service instance fails with an error")
        expected_msg = TapMessage.INSTANCE_IS_BOUND_TO_OTHER_INSTANCE.format(service_instance_2.name,
                                                                             service_instance_1.name,
                                                                             service_instance_1.id)
        assert_raises_command_execution_exception(1, expected_msg, service_instance_2.delete)
        step("Check that the service still exists")
        service_instance_2.ensure_on_service_list()
        step("Check that the services are still bound")
        binding.ensure_on_bindings_list()

        step("Get rid of binding")
        binding.delete()
        binding.ensure_not_on_bindings_list()
        service_instance_1.ensure_service_state(TapEntityState.RUNNING)

