#
# Copyright (c) 2016 Intel Corporation
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
from modules.constants import TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.markers import components, incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import KubernetesCluster, Organization, ServiceInstance, ServiceType, Space
from modules import test_names


logged_components = (TAP.demiurge, TAP.kubernetes_broker)
pytestmark = [components.demiurge, components.kubernetes_broker]


@incremental
@priority.high
# @pytest.mark.skipif(not config.CONFIG["kubernetes"], reason="No point to run without kuberentes")
class TestCluster:
    CLUSTERED_TAG = "clustered"

    def test_0_no_clusters_for_new_organization(self, class_context):
        step("Get list of clusters")
        clusters_before = KubernetesCluster.demiurge_api_get_list()
        step("Create organization and space")
        self.__class__.test_org = Organization.api_create(class_context)
        self.__class__.test_space = Space.api_create(org=self.test_org)
        step("Check that there are no new clusters created")
        clusters_after = KubernetesCluster.demiurge_api_get_list()
        assert len(clusters_before) == len(clusters_after)

    def test_1_create_service_instance(self):
        step("Get list of services to retrieve a {} service".format(self.CLUSTERED_TAG))
        services = ServiceType.api_get_list_from_marketplace(space_guid=self.test_space.guid)
        service = next((s for s in services if self.CLUSTERED_TAG in s.label), None)
        if service is None:
            raise AssertionError("No {} service available".format(self.CLUSTERED_TAG))

        step("Create instance")
        self.__class__.test_instance = ServiceInstance.api_create(
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

        step("Check that the cluster is gone")
        clusters = KubernetesCluster.demiurge_api_get_list()
        assert self.cluster not in clusters
