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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CliService, CliOffering
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_command_execution_exception


logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service, TAP.cli)]


@pytest.fixture(scope="module")
def offering(session_context, tap_cli):
    return CliOffering.create(context=session_context, tap_cli=tap_cli)


@pytest.mark.usefixtures("cli_login")
class TestCliBinding:
    SHORT = False

    @pytest.fixture(scope="class")
    def service_instance_1(self, class_context, tap_cli, offering):
        return CliService.create(
            context=class_context,
            offering_name=offering.name,
            plan=offering.plans[0],
            tap_cli=tap_cli)

    @pytest.fixture(scope="class")
    def service_instance_2(self, class_context, tap_cli, offering):
        return CliService.create(
            context=class_context,
            offering_name=offering.name,
            plan=offering.plans[0],
            tap_cli=tap_cli)

    @pytest.fixture(scope="class")
    def nonexistent_service(self, tap_cli, offering):
        return CliService(
            name=generate_test_object_name(separator="-"),
            offering_name=offering.name,
            plan=offering.plans[0],
            tap_cli=tap_cli)

    @pytest.fixture(scope="function")
    def cleanup_bindings(self, service_instance_1, service_instance_2, request):
        def fin():
            try:
                service_instance_2.unbind(service_instance_1)
                service_instance_1.unbind(service_instance_2)
            except:
                pass
        request.addfinalizer(fin)

    @pytest.mark.usefixtures("cleanup_bindings")
    @priority.high
    def test_bind_and_unbind_services(self, service_instance_1, service_instance_2):
        step("Bind one service instance to another")
        service_instance_2.bind(service_instance_1)
        step("Check that the services are bound")
        output = service_instance_1.get_bindings()
        assert service_instance_2.name in output
        step("Unbind service instance")
        service_instance_2.unbind(service_instance_1)
        step("Check that the services are not bound")
        output = service_instance_1.get_bindings()
        assert service_instance_2.name not in output

    @priority.low
    def test_cannot_bind_invalid_service(self, service_instance_1, nonexistent_service):
        step("Check that attempt to bind invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        assert_raises_command_execution_exception(1, expected_msg, nonexistent_service.bind, service_instance_1)

    @priority.low
    def test_cannot_bind_service_to_invalid_service(self, service_instance_1, nonexistent_service):
        step("Check that attempt to bind to invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        assert_raises_command_execution_exception(1, expected_msg, service_instance_1.bind, nonexistent_service)

    @priority.low
    def test_cannot_unbind_invalid_service(self, service_instance_1, nonexistent_service):
        step("Check that attempt to unbind invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        assert_raises_command_execution_exception(1, expected_msg, nonexistent_service.unbind, service_instance_1)

    @priority.low
    def test_cannot_unbind_service_from_invalid_service(self, service_instance_1, nonexistent_service):
        step("Check that attempt to unbind from invalid service instance will return error")
        expected_msg = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(nonexistent_service.name)
        assert_raises_command_execution_exception(1, expected_msg, service_instance_1.unbind, nonexistent_service)

    @priority.low
    @pytest.mark.usefixtures("cleanup_bindings")
    def test_cannot_delete_bound_service(self, service_instance_1, service_instance_2):
        step("Bind service instances")
        service_instance_2.bind(service_instance_1)
        assert service_instance_2.name in service_instance_1.get_bindings()
        step("Check that an attempt to delete bound service instance fails with an error")
        expected_msg = TapMessage.INSTANCE_IS_BOUND_TO_OTHER_INSTANCE.format(service_instance_2.name,
                                                                             service_instance_1.name,
                                                                             service_instance_1.id)
        assert_raises_command_execution_exception(1, expected_msg, service_instance_2.delete)
        step("Check that the service still exists")
        service_instance_2.ensure_on_service_list()
        step("Check that the services are still bound")
        assert service_instance_2.name in service_instance_1.get_bindings()


class TestCliBindingShortCommand(TestCliBinding):
    SHORT = True

