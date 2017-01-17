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

from modules.constants import TapEntityState
from modules.markers import long, priority
from modules.tap_logger import step
from modules.tap_object_model import CliService
from tap_component_config import offerings_as_parameters


@pytest.mark.usefixtures("cli_login")
class TestCreatingServiceInstancesViaCli:

    @long
    @priority.low
    @pytest.mark.parametrize("service_label,plan_name", offerings_as_parameters)
    @pytest.mark.bugs("DPNG-14838 GearPump instance cannot be created")
    @pytest.mark.bugs("DPNG-13981 Gearpump broker can't create new instance - 403 forbidden")
    @pytest.mark.bugs("DPNG-13185 Hive, zookeeper instances fail to be deleted")
    @pytest.mark.bugs("DPNG-14805 Cannot remove instance hdfs in plain-dir and encrypted-dir")
    @pytest.mark.bugs("DPNG-11192 TAP NG - get scoring engine running in TAP 0.8.0")
    def test_create_and_delete_instance_all(self, context, service_label, plan_name, tap_cli):
        """
        <b>Description:</b>
        Create service instance, check if it's shown in service instances list and remove it.

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
