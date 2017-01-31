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

from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CatalogState, ServiceInstance

logged_components = (TAP.catalog,)
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogState:

    @priority.high
    def test_get_stable_state(self, class_context):
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
        3. If catalog is unstable, skip test.
        """
        step("Get catalog stable state")
        response = CatalogState.get_stable_state()
        stable = response["stable"]
        message = response["message"]
        if stable is True:
            step("Stable is true, add unstable instance")
            instance = ServiceInstance.create_with_name(class_context, offering_label=ServiceLabels.RABBIT_MQ,
                                                        plan_name=ServicePlan.SINGLE_SMALL)
            response = CatalogState.get_stable_state()
            stable = response["stable"]
            assert stable is False
            instance.ensure_running()
        else:
            pytest.skip("Instances are unstable:{}".format(message))
