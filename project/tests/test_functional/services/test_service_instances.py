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

from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
from tests.fixtures import assertions

logged_components = (TAP.service_catalog, TAP.api_service)
pytestmark = [pytest.mark.components(TAP.service_catalog, TAP.api_service)]


class TestTapServiceInstance:
    @pytest.fixture(scope="function")
    def instance(self, context):
        instance = ServiceInstance.create_with_name(context=context, offering_label=ServiceLabels.KAFKA,
                                                    plan_name=ServicePlan.SHARED)
        instance.ensure_running()
        return instance

    @priority.medium
    def test_create_and_delete_service_instance(self, instance):
        """
        <b>Description:</b>
        Check that service instance can be created and deleted.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if service instance can be created and deleted.

        <b>Steps:</b>
        1. Create service instance.
        2. Check that instance is on the service instance list.
        3. Stop service instance.
        4. Delete service instance.
        5. Check that service instance on the list.
        """
        step("Get service instances list from ApiService")
        api_service_instances_list = ServiceInstance.get_list()
        step("Check if instance is on the list")
        assert instance in api_service_instances_list
        step("Stop service instance")
        instance.stop()
        instance.ensure_stopped()
        step("Delete service instance")
        instance.delete()
        step("Ensure instance is not on the list")
        assertions.assert_not_in_with_retry(instance, ServiceInstance.get_list)
