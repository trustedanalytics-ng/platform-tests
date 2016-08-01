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

import time

import pytest
from retry import retry

import config
from modules.constants import ServiceTag, TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import KubernetesCluster, Organization, ServiceInstance, ServiceType, Space
from modules import test_names


logged_components = (TAP.demiurge, TAP.kubernetes_broker)
pytestmark = [priority.high, pytest.mark.components(TAP.demiurge, TAP.kubernetes_broker)]


@incremental
@priority.high
@pytest.mark.skipif(not config.kubernetes, reason="No point to run without kubernetes")
class TestCluster:

    def test_0_no_clusters_for_new_organization(self, class_context):
        step("Get list of clusters")
        clusters_before = KubernetesCluster.demiurge_api_get_list()
        step("Create organization and space")
        self.__class__.test_org = Organization.api_create(class_context)
        self.__class__.test_space = Space.api_create(org=self.test_org)
        step("Check that there are no new clusters created")
        clusters_after = KubernetesCluster.demiurge_api_get_list()
        assert len(clusters_before) == len(clusters_after)

    def test_1_create_service_instance(self, class_context):
        step("Get list of services to retrieve a {} service".format(ServiceTag.K8S))
        services = ServiceType.api_get_list_from_marketplace(space_guid=self.test_space.guid)
        service = next((s for s in services if ServiceTag.K8S in s.tags), None)
        if service is None:
            raise AssertionError("No {} service available".format(ServiceTag.K8S))

        step("Create instance")
        self.__class__.test_instance = ServiceInstance.api_create(
            context=class_context,
            org_guid=self.test_org.guid,
            space_guid=self.test_space.guid,
            name=test_names.generate_test_object_name(short=True),
            service_label=service.label,
            service_plan_guid=service.service_plans[0]["guid"]
        )

        step("Check that the instance is on the list")
        instances = ServiceInstance.api_get_list(space_guid=self.test_space.guid)
        assert self.test_instance in instances

        step("Check that new cluster is created")
        self.__class__.cluster = KubernetesCluster.demiurge_api_get(name=self.test_org.guid)

    def test_2_delete_cluster(self):

        @retry(UnexpectedResponseError, tries=50, delay=30)
        def delete_instance_with_retry():
            self.test_instance.api_delete()

        step("Delete the instance and check it's no longer on the list")
        delete_instance_with_retry()

        step("Check the time after which the cluster should be removed")
        wait_before_remove_cluster_sec = KubernetesCluster.wait_before_removing_cluster()

        if int(wait_before_remove_cluster_sec) <= 60:
            step("Wait until the cluster is deleted.")
            time.sleep(int(wait_before_remove_cluster_sec))
            step("Check that the cluster is gone")
            clusters = KubernetesCluster.demiurge_api_get_list()
            cluster = next((c for c in clusters if self.cluster.name == c.name), None)
            assert cluster is None, "Cluster is still on the list"
