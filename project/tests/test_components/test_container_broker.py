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

import retry

from modules.constants import ContainerBrokerHttpStatus, TapEntityState, Guid, ServiceLabels, TapComponent as TAP
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogServiceInstance, ContainerBrokerInstance, CatalogService, KubernetesPod
from tests.fixtures import assertions


logged_components = (TAP.catalog, TAP.container_broker, )


@pytest.mark.usefixtures("open_tunnel")
class TestContainerBroker:
    TEST_OFFERING_LABEL_A = ServiceLabels.PSQL
    TEST_OFFERING_LABEL_B = ServiceLabels.RABBIT_MQ

    @pytest.fixture(scope="class")
    def catalog_offerings(self):
        log_fixture("CATALOG: Get list of available offerings")
        offerings = CatalogService.get_list()
        return offerings

    def _create_catalog_instance(self, context, offering):
        log_fixture("CATALOG: Create an example service instance for offering {}".format(offering.name))
        catalog_instance = CatalogServiceInstance.create(context, service_id=offering.id,
                                                         plan_id=offering.plans[0].id, state=TapEntityState.REQUESTED)
        catalog_instance.ensure_in_state(expected_state=TapEntityState.RUNNING)
        return catalog_instance

    @retry.retry(AssertionError, tries=30, delay=2)
    def _assert_pod_count_with_retry(self, instance_id, expected_pod_count):
        all_pods = KubernetesPod.get_list()
        pods = [p for p in all_pods if p.instance_id_label == instance_id]
        assert len(pods) == expected_pod_count, "Number of pods: {}, expected: {}".format(len(pods), expected_pod_count)
        return pods

    @retry.retry(AssertionError, tries=12, delay=2)
    def _assert_binding_in_pod_with_retry(self, instance_id, offering_label):
        all_pods = KubernetesPod.get_list()
        pods = [p for p in all_pods if p.instance_id_label == instance_id]
        assert len(pods) > 0, "No pods found for instance"
        bindings = [c["name"] for c in pods[0].containers]
        assert offering_label in bindings, "Binding for {} not found in pod. Bindings: {}".format(offering_label,
                                                                                                  ",".join(bindings))

    @pytest.fixture(scope="class")
    def offering_a(self, catalog_offerings):
        offering = next((o for o in catalog_offerings if o.name == self.TEST_OFFERING_LABEL_A), None)
        assert offering is not None, "No such offering {}".format(self.TEST_OFFERING_LABEL_A)
        return offering

    @pytest.fixture(scope="class")
    def offering_b(self, catalog_offerings):
        offering = next((o for o in catalog_offerings if o.name == self.TEST_OFFERING_LABEL_B), None)
        assert offering is not None, "No such offering {}".format(self.TEST_OFFERING_LABEL_B)
        return offering

    @pytest.fixture(scope="class")
    def catalog_instance_a(self, class_context, offering_a):
        return self._create_catalog_instance(context=class_context, offering=offering_a)

    @pytest.fixture(scope="class")
    def catalog_instance_b(self, class_context, offering_b):
        return self._create_catalog_instance(context=class_context, offering=offering_b)

    @pytest.mark.bugs("DPNG-12413 When binding instances, dst instance does not have src instance envs in its pod")
    @pytest.mark.components(TAP.catalog)
    def test_create_and_destroy_service_instance(self, context, offering_a):
        step("CATALOG: Create service instance in {} state".format(TapEntityState.REQUESTED))
        # REQUESTED state will trigger monitor to grab the instance from catalog and send it to container-broker queue
        instance = CatalogServiceInstance.create(context, service_id=offering_a.id, plan_id=offering_a.plans[0].id,
                                                 state=TapEntityState.REQUESTED)
        step("Wait for the monitor and container-broker to move the instance to RUNNING state")
        instance.ensure_in_state(expected_state=TapEntityState.RUNNING)

        step("KUBERNETES: Check that corresponding pod exists and is running")
        pods = self._assert_pod_count_with_retry(instance_id=instance.id, expected_pod_count=1)
        assert pods[0].state == KubernetesPod.RUNNING

        step("CATALOG: Stop service instance")
        instance.stop()
        step("CATALOG: Destroy service instance and check it's gone")
        instance.destroy()
        assertions.assert_not_in_with_retry(instance, CatalogServiceInstance.get_list_for_service,
                                            service_id=offering_a.id)

        step("KUBERNETES: Check that the pod does not exist")
        self._assert_pod_count_with_retry(instance_id=instance.id, expected_pod_count=0)

    @pytest.mark.bugs("DPNG-12413 When binding instances, dst instance does not have src instance envs in its pod")
    @pytest.mark.components(TAP.catalog, TAP.container_broker)
    def test_bind_and_unbind_instances(self, offering_a, catalog_instance_a, catalog_instance_b):
        step("CONTAINER-BROKER: Bind two instances")
        src_instance = ContainerBrokerInstance(instance_id=catalog_instance_a.id)
        dst_instance = ContainerBrokerInstance(instance_id=catalog_instance_b.id)
        src_instance.bind(bound_instance_id=dst_instance.id)

        step("CATALOG: Check that the instances are bound")
        # dst instance should have bindings, src instance should not
        dst_catalog_instance = CatalogServiceInstance.get(service_id=catalog_instance_b.class_id,
                                                          instance_id=catalog_instance_b.id)
        dst_catalog_instance.ensure_bound(src_instance_id=src_instance.id)
        src_catalog_instance = CatalogServiceInstance.get(service_id=catalog_instance_a.class_id,
                                                          instance_id=catalog_instance_a.id)
        assert src_catalog_instance.bound_instance_ids == []

        step("KUBERNETES: Check if dst pod has src instance info")
        self._assert_binding_in_pod_with_retry(instance_id=dst_catalog_instance.id, offering_label=offering_a.name)

        step("CONTAINER-BROKER: Unbind the instances")
        src_instance.unbind(bound_instance_id=dst_instance.id)

        step("CATALOG: Check that the instances are not bound")
        dst_catalog_instance = CatalogServiceInstance.get(service_id=catalog_instance_b.class_id,
                                                          instance_id=catalog_instance_b.id)
        dst_catalog_instance.ensure_unbound(src_instance_id=src_instance.id)
        src_catalog_instance = CatalogServiceInstance.get(service_id=catalog_instance_a.class_id,
                                                          instance_id=catalog_instance_a.id)
        assert src_catalog_instance.bound_instance_ids == []

    @pytest.mark.components(TAP.catalog, TAP.container_broker)
    def test_get_instance_logs_in_container_broker(self, catalog_instance_a):
        step("CONTAINER-BROKER: Get instance logs")
        container_broker_instance = ContainerBrokerInstance(instance_id=catalog_instance_a.id)
        response = container_broker_instance.get_logs()
        assert isinstance(response, dict)

    @pytest.mark.bugs("DPNG-12413 When binding instances, dst instance does not have src instance envs in its pod")
    @pytest.mark.components(TAP.catalog, TAP.container_broker)
    def test_get_instance_envs_in_container_broker(self, catalog_instance_a):
        step("CONTAINER-BROKER: Get instance envs")
        container_broker_instance = ContainerBrokerInstance(instance_id=catalog_instance_a.id)
        response = container_broker_instance.get_envs()
        assert ContainerBrokerInstance.ENVS_KEY in response[0]

    @pytest.mark.bugs("DPNG-12415 container-broker: Insufficient information in error message")
    @pytest.mark.components(TAP.container_broker)
    def test_cannot_get_logs_with_incorrect_instance_id(self):
        non_existing_instance = ContainerBrokerInstance(instance_id=Guid.NON_EXISTING_GUID)
        expected_msg = ContainerBrokerHttpStatus.MSG_DEPLOYMENTS_NOT_FOUND.format(non_existing_instance.id)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                non_existing_instance.get_logs)

    @pytest.mark.bugs("DPNG-12415 container-broker: Insufficient information in error message")
    @pytest.mark.components(TAP.container_broker)
    def test_cannot_get_envs_with_incorrect_instance_id(self):
        non_existing_instance = ContainerBrokerInstance(instance_id=Guid.NON_EXISTING_GUID)
        expected_msg = ContainerBrokerHttpStatus.MSG_DEPLOYMENTS_NOT_FOUND.format(non_existing_instance.id)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                non_existing_instance.get_envs)
