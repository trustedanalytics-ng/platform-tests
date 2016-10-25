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

from datetime import datetime

import pytest

from modules.constants.services import ServiceLabels
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import ServiceInstance, ServiceOffering
from tests.fixtures import assertions


class TestServiceInstancesMonitoring:
    TESTED_APP_NAMES = {ServiceLabels.RSTUDIO}

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def marketplace_services(cls, test_space):
        log_fixture("Get list of available services from Marketplace")
        return ServiceOffering.get_list()

    def test_service_instances(self, context, test_org, marketplace_services):
        tested_service_types = [st for st in marketplace_services if st.label in self.TESTED_APP_NAMES]
        errors = []
        for service_type in tested_service_types:
            for plan in service_type.service_plans:
                try:
                    self._create_instance(context, test_org, plan, service_type)
                except Exception as e:
                    errors.append(e)
        assertions.assert_no_errors(errors)

    def _create_instance(self, context, test_org, plan, service_type):
        step("Create instance of {} ({} plan). Check it exists.".format(service_type.label, plan["name"]))
        service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        instance = ServiceInstance.api_create(
            context=context,
            org_guid=test_org.guid,
            space_guid=service_type.space_guid,
            service_label=service_type.label,
            name=service_instance_name,
            service_plan_guid=plan['guid']
        )
        assert instance is not None, "{} instance was not created".format(service_type)
        step("Delete the instance and check it no longer exists")
        instance.api_delete()
        instances = ServiceInstance.api_get_list(space_guid=service_type.space_guid,
                                                 service_type_guid=service_type.guid)
        assert instance not in instances, "{} instance was not deleted".format(service_type)
