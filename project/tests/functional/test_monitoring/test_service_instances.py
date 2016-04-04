#
# Copyright (c) 2015-2016 Intel Corporation
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

from datetime import datetime

import pytest

from modules.constants.services import ServiceLabels
from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import ServiceInstance, ServiceType


class ServiceInstancesMonitoring(TapTestCase):

    TESTED_APP_NAMES = {ServiceLabels.RSTUDIO}

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def marketplace_services(cls, test_org, test_space):
        cls.test_org = test_org
        cls.step("Get list of available services from Marketplace")
        cls.marketplace_services = ServiceType.api_get_list_from_marketplace(test_space.guid)

    def test_service_instances(self):
        tested_service_types = [st for st in self.marketplace_services if st.label in self.TESTED_APP_NAMES]
        for service_type in tested_service_types:
            for plan in service_type.service_plans:
                with self.subTest(service=service_type.label, plan=plan["name"]):
                    self.step("Create instance of {} ({} plan). Check it exists.".format(service_type.label,
                                                                                         plan["name"]))
                    service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    instance = ServiceInstance.api_create(
                        org_guid=self.test_org.guid,
                        space_guid=service_type.space_guid,
                        service_label=service_type.label,
                        name=service_instance_name,
                        service_plan_guid=plan['guid']
                    )
                    self.assertIsNotNone(instance, "{} instance was not created".format(service_type))
                    self.step("Delete the instance and check it no longer exists")
                    instance.api_delete()
                    instances = ServiceInstance.api_get_list(space_guid=service_type.space_guid,
                                                             service_type_guid=service_type.guid)
                    self.assertNotIn(instance, instances, "{} instance was not deleted".format(service_type))
