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

from modules.constants import TapComponent as TAP, TapEntityState
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CatalogState, CatalogInstance

logged_components = (TAP.catalog,)
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogState:
    STOP_REQ = TapEntityState.STOP_REQ
    STOPPED = TapEntityState.STOPPED
    STARTING = TapEntityState.STARTING
    RUNNING = TapEntityState.RUNNING
    FAILURE = TapEntityState.FAILURE

    def remove_unstable_instances(self):
        all_instances = CatalogInstance.get_all()
        for i in all_instances:
            if i.state not in [self.RUNNING, self.STOPPED, self.FAILURE]:
                instance = CatalogInstance.get(instance_id=i.id)
                instance.update(field_name="state", value=self.FAILURE)

    @priority.high
    def test_get_stable_state(self):
        """
        <b>Description:</b>
        Checks catalog stable state

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test checks if catalog state is stable or unstable.

        <b>Steps:</b>
        1. Get catalog state.
        2. If catalog is stable, add unstable instance and check if state is unstable.
        3. If catalog is unstable, remove all unstable instances and check if state is stable.
        """
        step("Get catalog stable state")
        response = CatalogState.get_stable_state()
        stable = response["stable"]
        if stable is True:
            step("Stable is true, add unstable instance")
            all_instances = CatalogInstance.get_all()
            for i in all_instances:
                if i.state == self.STOPPED:
                    instance = CatalogInstance.get(instance_id=i.id)
                    instance.update(field_name="state", value=self.STARTING)
                    break
                if i.state == self.RUNNING:
                    instance = CatalogInstance.get(instance_id=i.id)
                    instance.update(field_name="state", value=self.STOP_REQ)
                    break
            response = CatalogState.get_stable_state()
            stable = response["stable"]
            assert stable is False
        else:
            step("Stable is false, remove all unstable instances")
            self.remove_unstable_instances()
            response = CatalogState.get_stable_state()
            stable = response["stable"]
            assert stable is True
