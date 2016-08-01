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

import config
from modules.constants import TapComponent as TAP
from modules.markers import incremental, priority
from modules.tap_object_model import ServiceInstance, ServiceType
from modules.tap_logger import step
from modules import test_names

logged_components = (TAP.kubernetes_broker,)
pytestmark = [priority.medium, pytest.mark.components(TAP.kubernetes_broker)]


@incremental
@pytest.mark.skipif(not config.kubernetes, reason="No point to run without kubernetes")
class TestKubernetes:
    service_name = test_names.generate_test_object_name(short=True)
    test_service = None
    test_instance = None

    def test_1_create_dynamic_service(self, core_org, core_space):
        step("Create new service offering in kubernetes broker")
        service_name = ServiceType.k8s_broker_create_dynamic_service(core_org.guid, core_space.guid,
                                                                     service_name=self.service_name)
        step("Check the new offering is in kubernetes-broker catalog")
        catalog = ServiceType.k8s_broker_get_catalog()
        kubernetes_service = next((s for s in catalog if s.label == service_name), None)
        assert kubernetes_service is not None

    def test_2_enable_service_access(self, core_space):
        step("Check service is available in cloud foundry")
        cf_services = ServiceType.cf_api_get_list(name=self.service_name, get_plans=True)
        assert len(cf_services) == 1
        self.__class__.test_service = cf_services[0]

        step("Enable service access")
        self.test_service.cf_api_enable_service_access()
        self.test_service.space_guid = core_space.guid

        step("Check the service is visible in marketplace")
        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=core_space.guid)
        assert self.test_service in marketplace

    def test_3_create_instance_of_dynamic_kubernetes_service(self, class_context, core_org, core_space):
        step("Create instance of the new service and check it's on the list")
        self.__class__.test_instance = ServiceInstance.api_create(
            context=class_context,
            org_guid=core_org.guid,
            space_guid=core_space.guid,
            service_label=self.service_name,
            service_plan_guid=self.test_service.service_plans[0]["guid"]
        )
        instances = ServiceInstance.api_get_list(space_guid=core_space.guid)
        self.test_instance.ensure_created()
        assert self.test_instance in instances

    def test_4_delete_instance_of_kubernetes_service(self, core_space):
        step("Delete instance and check it's no longer on the list")
        self.test_instance.api_delete()
        instances = ServiceInstance.api_get_list(space_guid=core_space.guid)
        assert self.test_instance not in instances

    def test_5_disable_service_access(self, core_space):
        step("Disable service access")
        self.test_service.cf_api_disable_service_access()
        step("Check the service is not visible in marketplace")
        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=core_space.guid)
        assert self.test_service not in marketplace

    def test_6_delete_dynamic_service(self):
        step("Delete created dynamic service")
        ServiceType.k8s_broker_delete_dynamic_service(service_name=self.service_name)
        step("Check that deleted service is not in kubernetes-broker catalog")
        catalog = ServiceType.k8s_broker_get_catalog()
        kubernetes_service = next((s for s in catalog if s.label == self.service_name), None)
        assert kubernetes_service is None
