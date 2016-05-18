#
# Copyright (c) 2015-2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest
from retry import retry

from configuration import config
from modules.exceptions import UnexpectedResponseError
from modules.markers import incremental, priority, components
from modules.tap_object_model import ServiceInstance, ServiceType
from modules.tap_logger import step
from modules import test_names


pytestmark = [priority.medium, components.kubernetes_broker]


@incremental
@pytest.mark.skip("Skipped until dynamic service deletion is implemented")
@pytest.mark.skipif(not config.CONFIG["kubernetes"], reason="No point to run without kuberentes")
class TestKubernetes:
    service_name = test_names.generate_test_object_name(short=True)
    test_service = None
    test_instance = None

    @pytest.fixture(scope="class", autouse=True)
    def cleanup(self, request):
        def fin():
            if self.test_service is not None:
                self.test_service.cf_api_disable_service_access()
        request.addfinalizer(fin)

    @retry(UnexpectedResponseError, tries=10, delay=3)
    def _delete_with_retry(self, instance):
        instance.api_delete()

    def test_create_dynamic_service(self, core_org, core_space):
        step("Create new service offering in kubernetes broker")
        service_name = ServiceType.k8s_broker_create_dynamic_service(core_org.guid, core_space.guid,
                                                                     service_name=self.service_name)
        step("Check the new offering is in kubernetes-broker catalog")
        catalog = ServiceType.k8s_broker_get_catalog()
        kubernetes_service = next((s for s in catalog if s.label == service_name), None)
        assert kubernetes_service is not None

    def test_enable_service_access(self, core_space):
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

    def test_create_instance_of_kubernetes_service(self, core_org, core_space):
        step("Create instance of the new service and check it's on the list")
        self.__class__.test_instance = ServiceInstance.api_create(
            org_guid=core_org.guid,
            space_guid=core_space.guid,
            service_label=self.service_name,
            service_plan_guid=self.test_service.service_plans[0]["guid"]
        )
        instances = ServiceInstance.api_get_list(space_guid=core_space.guid)
        assert self.test_instance in instances

    def test_delete_instance_of_kubernetes_service(self, core_space):
        step("Delete instance and check it's no longer on the list")
        self._delete_with_retry(self.test_instance)
        instances = ServiceInstance.api_get_list(space_guid=core_space.guid)
        assert self.test_instance not in instances

    def test_disable_service_access(self, core_space):
        step("Disable service access")
        self.test_service.cf_api_disable_service_access()
        step("Check the service is not visible in marketplace")
        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=core_space.guid)
        assert self.test_service not in marketplace


