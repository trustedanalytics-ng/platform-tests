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

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import ServiceLabels, TapComponent as TAP
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceType
from tests.fixtures.test_data import TestData

logged_components = (TAP.service_catalog, TAP.service_exposer)
pytestmark = [components.service_catalog, components.service_exposer]


class TestDataScienceInstances(object):

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def marketplace_services(cls, test_org, test_space):
        step("Get marketplace services")
        cls.marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)

    @priority.high
    @pytest.mark.parametrize("service_label", [ServiceLabels.JUPYTER])
    def test_create_and_delete_service_instances(self, service_label):
        service_type = next((s for s in self.marketplace if s.label == service_label), None)
        assert service_type is not None, "{} service is not available in Marketplace".format(service_label)
        plan = next(iter(service_type.service_plans))
        step("Create service instance")
        instance = ServiceInstance.api_create(
            org_guid=TestData.test_org.guid,
            space_guid=TestData.test_space.guid,
            service_label=service_type.label,
            service_plan_guid=plan["guid"]
        )
        validator = ApplicationStackValidator(TapTestCase(), instance)
        validator.validate(validate_application=False)
        instance.api_delete()
        validator.validate_removed()
