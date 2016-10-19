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

from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
from tests.fixtures.assertions import assert_in_with_retry

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog),
              pytest.mark.skip(reason="DPNG-11125 api-service: endpoint for adding offerings from jar archives")]

TESTED_ROLES = ["user", "admin"]


@priority.high
@pytest.mark.parametrize("role", TESTED_ROLES)
def test_create_instance_as_authorized_user(context, role, sample_service, test_user_clients):
    client = test_user_clients[role]
    step("Create an instance")
    instance = ServiceInstance.create_with_name(context, offering_label=sample_service.label,
                                                plan_name=sample_service.service_plans[0]["entity"]["name"],
                                                client=client)
    step("Check that service instance is present")
    assert_in_with_retry(instance, ServiceInstance.get_list, client=client)
