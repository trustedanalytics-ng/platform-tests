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
from modules.markers import components, incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, ServiceType, AtkInstance


logged_components = (TAP.service_catalog, TAP.service_exposer, TAP.application_broker)
pytestmark = [components.service_catalog, components.application_broker, components.service_exposer]


@incremental
@priority.high
class TestDataScienceAtkInstance:

    atk_bindings = None
    atk_instance = None
    atk_from_data_science_list = None
    validator = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def marketplace(cls, test_org, test_space):
        cls.marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)

    @pytest.mark.usefixtures("core_space")
    def test_0_get_reference_atk_bindings(self, core_space):
        step("Get services bound to atk in the reference space")
        ref_atk_app = next((a for a in Application.api_get_list(core_space.guid) if a.name == "atk"), None)
        assert ref_atk_app is not None, "ATK app not found in the reference space"
        self.__class__.atk_bindings = [s[0]["label"] for s in ref_atk_app.cf_api_env()["VCAP_SERVICES"].values()]

    def test_1_create_atk_instance(self, class_context, test_org, test_space):
        step("Get tested service type")
        service_type = next(s for s in self.marketplace if s.label == ServiceLabels.ATK)
        plan = next(iter(service_type.service_plans))
        step("Create atk instance")
        self.__class__.atk_instance = ServiceInstance.api_create(
            context=class_context,
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=service_type.label,
            service_plan_guid=plan["guid"]
        )

    def test_2_check_atk_instance_exists(self, test_org):
        step("Find atk instance on the data science instances list")
        data_science_atk_list = AtkInstance.api_get_list_from_data_science_atk(test_org.guid)
        self.__class__.atk_from_data_science_list = next((i for i in data_science_atk_list
                                                          if i.name == self.atk_instance.name), None)
        step("Check that service instance exists in data science atk list")
        assert self.atk_from_data_science_list is not None, "Atk instance not found in data science list"

    @pytest.mark.usefixtures("admin_user")
    def test_3_validate_atk_instance_creator(self, admin_user):
        step("Check atk instance creator")
        assert self.atk_from_data_science_list.creator_name == admin_user.username, "Atk creator name doesn't match"
        assert self.atk_from_data_science_list.creator_guid == admin_user.guid, "Atk creator guid doesn't match"

    def test_4_validate_atk_app_and_bindings(self):
        self.__class__.validator = ApplicationStackValidator(self.atk_instance)
        self.validator.validate(expected_bindings=self.atk_bindings)

    def test_5_validate_delete_atk_instance(self):
        step("Delete atk instance")
        self.atk_instance.api_delete()
        self.validator.validate_removed()
