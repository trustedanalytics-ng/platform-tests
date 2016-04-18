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

import unittest

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import ServiceLabels, TapComponent as TAP, Priority
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, incremental
from modules.tap_object_model import Application, Organization, ServiceInstance, ServiceType, Space, AtkInstance, User
from tests.fixtures import setup_fixtures, teardown_fixtures


@log_components()
@incremental(Priority.high)
@components(TAP.service_catalog, TAP.service_exposer, TAP.application_broker)
class DataScienceAtkInstance(TapTestCase):
    atk_bindings = None
    atk_instance = None
    atk_from_data_science_list = None
    validator = None

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create()
        cls.test_space = Space.api_create(cls.test_org)
        cls.step("Get marketplace services")
        cls.marketplace = ServiceType.api_get_list_from_marketplace(cls.test_space.guid)

    def test_0_get_reference_atk_bindings(self):
        self.step("Get services bound to atk in the reference space")
        ref_space_guid = setup_fixtures.get_reference_space().guid
        ref_atk_app = next((a for a in Application.api_get_list(ref_space_guid) if a.name == "atk"), None)
        self.assertIsNotNone(ref_atk_app, "ATK app not found in the reference space")
        self.__class__.atk_bindings = [s[0]["label"] for s in ref_atk_app.cf_api_env()["VCAP_SERVICES"].values()]

    def test_1_create_atk_instance(self):
        self.step("Get tested service type")
        service_type = next(s for s in self.marketplace if s.label == ServiceLabels.ATK)
        plan = next(iter(service_type.service_plans))
        self.step("Create atk instance")
        self.__class__.atk_instance = ServiceInstance.api_create(
            org_guid=self.test_org.guid,
            space_guid=self.test_space.guid,
            service_label=service_type.label,
            service_plan_guid=plan["guid"]
        )

    @unittest.skip("DPNG-6832")
    def test_2_check_atk_instance_exists(self):
        self.step("Find atk instance on the data science instances list")
        data_science_atk_list = AtkInstance.api_get_list_from_data_science_atk(self.test_org.guid)
        self.__class__.atk_from_data_science_list = next((i for i in data_science_atk_list
                                                          if i.name == self.atk_instance.name), None)
        self.step("Check that service instance exists in data science atk list")
        self.assertIsNotNone(self.atk_from_data_science_list, "Atk instance not found in data science list")

    @unittest.skip("DPNG-6832")
    def test_3_validate_atk_instance_creator(self):
        admin_user = User.get_admin()
        self.step("Check atk instance creator")
        self.assertEqual(self.atk_from_data_science_list.creator_name, admin_user.username,
                         "Atk creator name doesn't match")
        self.assertEqual(self.atk_from_data_science_list.creator_guid, admin_user.guid,
                         "Atk creator guid doesn't match")

    @unittest.skip("DPNG-6832")
    def test_4_validate_atk_app_and_bindings(self):
        self.__class__.validator = ApplicationStackValidator(self, self.atk_instance)
        self.validator.validate(expected_bindings=self.atk_bindings)

    @unittest.skip("DPNG-6832")
    def test_5_validate_delete_atk_instance(self):
        self.step("Delete atk instance")
        self.atk_instance.api_delete()
        self.validator.validate_removed()
