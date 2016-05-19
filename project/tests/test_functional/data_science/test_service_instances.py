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
from modules.tap_object_model import ServiceInstance, ServiceType
from tests.fixtures.test_data import TestData


logged_components = (TAP.service_catalog, TAP.service_exposer)
pytestmark = [components.service_catalog, components.service_exposer]


class DataScienceInstances(TapTestCase):

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def marketplace_services(cls, test_org, test_space):
        cls.step("Get marketplace services")
        cls.marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)

    @priority.high
    def test_create_and_delete_service_instances(self):
        services = [ServiceLabels.JUPYTER, ServiceLabels.RSTUDIO]
        for service_type in [s for s in self.marketplace if s.label in services]:
            plan = next(iter(service_type.service_plans))
            with self.subTest(service=service_type.label):
                self.step("Create service instance")
                instance = ServiceInstance.api_create(
                    org_guid=TestData.test_org.guid,
                    space_guid=TestData.test_space.guid,
                    service_label=service_type.label,
                    service_plan_guid=plan["guid"]
                )
                validator = ApplicationStackValidator(self, instance)
                validator.validate(validate_application=False)
                instance.api_delete()
                validator.validate_removed()
