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
from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP
from modules.markers import incremental, priority, components
from modules.tap_object_model import KubernetesInstance, ServiceInstance, ServiceType
from modules.tap_logger import step


logged_components = (TAP.kubernetes_broker,)
pytestmark = [priority.medium, components.kubernetes_broker]


@incremental
@pytest.mark.skipif(not config.kubernetes, reason="No point to run without kubernetes")
class TestExposeKubernetesService:
    service_label = ServiceLabels.MONGO_DB_30_MULTINODE
    plan_name = ServicePlan.CLUSTERED

    def test_0_create_instance_of_kubernetes_service(self, test_org, test_space):
        step("Retrieve example kubernetes service from marketplace")
        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=test_space.guid)
        k8s_service = next((s for s in marketplace if s.label == self.service_label), None)
        assert k8s_service is not None, "{} not available".format(self.service_label)
        plan_guid = next((p["guid"] for p in k8s_service.service_plans if p["name"] == self.plan_name), None)
        assert plan_guid is not None, "Plan {} not available".format(self.plan_name)
        step("Create instance of the k8s service")
        self.__class__.test_instance = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=self.service_label,
            service_plan_guid=plan_guid
        )
        step("Wait until the instance is running")
        self.__class__.k8s_instance = KubernetesInstance.from_service_instance(
            guid=self.test_instance.guid,
            plan_guid=plan_guid,
            space_guid=test_space.guid,
            org_guid=test_org.guid
        )
        self.k8s_instance.ensure_running_in_cluster()
        step("Check instance has correct status on TAP")
        self.test_instance.ensure_created()

    @pytest.mark.bugs("DPNG-7739 Scope 'console.admin' not present for client_id 'cf'")
    def test_1_check_instance_is_not_visible(self, test_org, test_space):
        step("Get instance info from kubernetes-broker")
        self.k8s_instance.get_info()
        step("Check that instance is not visible")
        assert self.k8s_instance.is_visible is False

    def test_2_expose_service_instance(self, test_org, test_space):
        step("Expose service instance")
        self.k8s_instance.change_visibility(visibility=True)
        step("Check that instance is exposed")
        self.k8s_instance.get_info()
        assert self.k8s_instance.is_visible
        step("Check instance visibility on the exposed services list")
        k8s_instances = KubernetesInstance.get_list(org_guid=test_org.guid, space_guid=test_space.guid)
        assert self.k8s_instance in k8s_instances

    def test_6_delete_instance(self):
        step("Delete the instance")
        self.k8s_instance.delete()
