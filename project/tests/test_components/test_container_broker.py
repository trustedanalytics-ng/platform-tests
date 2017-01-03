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

import config
from fixtures.k8s_templates import template_example
from modules.constants import ContainerBrokerHttpStatus, TapEntityState, Guid, ServiceLabels, TapComponent as TAP
from modules.http_client import HttpMethod
from modules.http_client.http_client_configuration import HttpClientConfiguration
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.http_client_type import HttpClientType
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogServiceInstance, ContainerBrokerInstance, CatalogService, KubernetesPod
from modules.tap_object_model import ServiceOffering
from tests.fixtures import assertions

logged_components = (TAP.catalog, TAP.container_broker, )


@pytest.mark.usefixtures("open_tunnel")
class TestContainerBroker:
    TEST_OFFERING_LABEL_A = ServiceLabels.PSQL
    TEST_OFFERING_LABEL_B = ServiceLabels.RABBIT_MQ
    POSTGRESQL_ENV_NAME = "SERVICES_BOUND_POSTGRESQL_93"
    INVALID_PARAM = "xxxxxxxx"
    HOSTNAME = "kolcz1"
    PORT = 4222
    INVALID_PORT = 598

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

    def _get_configmap(self, tunnel, configmap_name_suffix):
        configmaps = tunnel._jump_client.ssh(["ssh", "-tt", "compute-master"] + ["kubectl", "get", "configmaps"])
        configmaps = str(configmaps)
        idx = configmaps.index(configmap_name_suffix)
        return configmaps[idx - 14:idx + len(configmap_name_suffix)]

    def _get_secret(self, tunnel, secret_name_suffix):
        secrets = tunnel._jump_client.ssh(["ssh", "-tt", "compute-master"] + ["kubectl", "get", "secret"])
        secrets = str(secrets)
        idx = secrets.index(secret_name_suffix)
        return secrets[idx - 14:idx + len(secret_name_suffix)]

    @retry.retry(AssertionError, tries=12, delay=2)
    def _send_request(self, url):
        configuration = HttpClientConfiguration(client_type=HttpClientType.BROKER, url=url)
        response = HttpClientFactory.get(configuration).request(method=HttpMethod.GET, path="",
                                                                raw_response=True, raise_exception=False)
        assert response.status_code == ContainerBrokerHttpStatus.CODE_OK
        return response

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
        envs = [c["env"] for c in pods[0].containers]
        env = next((e for e in envs[0] if e["name"] == self.POSTGRESQL_ENV_NAME), None)
        assert env is not None, "Env for {} not found in pod".format(offering_label)

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
    def offering_nats(self, class_context, api_service_admin_client):
        test_offering = ServiceOffering.create(class_context, template_body=template_example.nats_template["body"],
                                               client=api_service_admin_client)
        catalog_offerings = CatalogService.get_list()
        offering = next((o for o in catalog_offerings if o.name == test_offering.label), None)
        assert offering is not None, "No such offering {}".format(test_offering.label)
        return offering

    @pytest.fixture(scope="class")
    def catalog_instance_a(self, class_context, offering_a):
        return self._create_catalog_instance(context=class_context, offering=offering_a)

    @pytest.fixture(scope="class")
    def catalog_instance_b(self, class_context, offering_b):
        return self._create_catalog_instance(context=class_context, offering=offering_b)

    @pytest.fixture(scope="class")
    def catalog_instance_nats(self, class_context, offering_nats):
        return self._create_catalog_instance(context=class_context, offering=offering_nats)

    @pytest.fixture(scope="class")
    def configmaps_list(self, class_context, open_tunnel):
        tunnel = open_tunnel
        out = tunnel._jump_client.ssh(["ssh", "-tt", "compute-master"] + ["kubectl", "get", "secret"])

    @pytest.mark.components(TAP.catalog)
    def test_create_and_destroy_service_instance(self, context, offering_a):
        """
        <b>Description:</b>
        Create and destroy service instance

        <b>Input data:</b>
        Offering

        <b>Expected results:</b>
        It's possible to create and later destroy service instance

        <b>Steps:</b>
        - Create service instance and verify it's running
        - Destroy service instance and verify it was removed
        """
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

    @pytest.mark.components(TAP.catalog, TAP.container_broker)
    def test_bind_and_unbind_instances(self, offering_a, catalog_instance_a, catalog_instance_b):
        """
        <b>Description:</b>
        Bind two container broker instances to each other

        <b>Input data:</b>
        Two instances

        <b>Expected results:</b>
        It's possible to bind two instances to each other

        <b>Steps:</b>
        - Create two instances
        - Bind them to each other and verify they have a bond
        - Unbind the instances and verify that the bond was lost
        """
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
        """
        <b>Description:</b>
        Retrieve service instance logs from container broker

        <b>Input data:</b>
        Catalog broker instance

        <b>Expected results:</b>
        It's possible to retrieve logs from container broker

        <b>Steps:</b>
        - Create container broker instance
        - Ask for logs for newly created instance from service broker
        """
        step("CONTAINER-BROKER: Get instance logs")
        container_broker_instance = ContainerBrokerInstance(instance_id=catalog_instance_a.id)
        response = container_broker_instance.get_logs()
        assert isinstance(response, dict)

    @pytest.mark.components(TAP.catalog, TAP.container_broker)
    def test_get_instance_envs_in_container_broker(self, catalog_instance_a):
        """
        <b>Description:</b>
        Retrieve environment variables for instance from container broker

        <b>Input data:</b>
        Catalog broker instance

        <b>Expected results:</b>
        It's possible to retrieve all envs from instance

        <b>Steps:</b>
        - Create container broker instance
        - Retrieve the environment variables
        """
        step("CONTAINER-BROKER: Get instance envs")
        container_broker_instance = ContainerBrokerInstance(instance_id=catalog_instance_a.id)
        response = container_broker_instance.get_envs()
        assert ContainerBrokerInstance.ENVS_KEY in response[0]

    @pytest.mark.bugs("DPNG-12415 container-broker: Insufficient information in error message")
    @pytest.mark.components(TAP.container_broker)
    def test_cannot_get_logs_with_incorrect_instance_id(self):
        """
        <b>Description:</b>
        Retrieve logs from an non-existent instance

        <b>Input data:</b>
        Wrong instance id

        <b>Expected results:</b>
        It's not possible retrieve any logs

        <b>Steps:</b>
        - Create container broker instance with bad id
        - Retrieve the logs
        - Verify platform returned error
        """
        non_existing_instance = ContainerBrokerInstance(instance_id=Guid.NON_EXISTING_GUID)
        expected_msg = ContainerBrokerHttpStatus.MSG_DEPLOYMENTS_NOT_FOUND.format(non_existing_instance.id)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                non_existing_instance.get_logs)

    @pytest.mark.bugs("DPNG-12415 container-broker: Insufficient information in error message")
    @pytest.mark.components(TAP.container_broker)
    def test_cannot_get_envs_with_incorrect_instance_id(self):
        """
        <b>Description:</b>
        Retrieve envs from an non-existent instance

        <b>Input data:</b>
        Wrong instance id

        <b>Expected results:</b>
        It's not possible retrieve any environment variables

        <b>Steps:</b>
        - Create container broker instance with bad id
        - Retrieve the environment variables
        - Verify platform returned error
        """
        non_existing_instance = ContainerBrokerInstance(instance_id=Guid.NON_EXISTING_GUID)
        expected_msg = ContainerBrokerHttpStatus.MSG_DEPLOYMENTS_NOT_FOUND.format(non_existing_instance.id)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                non_existing_instance.get_envs)

    def test_get_core_components_version(self):
        """
        <b>Description:</b>
        Get version information about core components.

        <b>Input data:</b>
        Container broker instance.

        <b>Expected results:</b>
        Information about core components.

        <b>Steps:</b>
        - Get version about core components.
        - Verify if core component is on the list.
        """
        step("Get version information about core components")
        response = ContainerBrokerInstance.get_version()
        assert response is not None
        components = [c["name"] for c in response]
        assert TAP.auth_gateway in components

    def test_get_specific_configmap(self):
        """
        <b>Description:</b>
        Get specific configmap.

        <b>Input data:</b>
        Container broker instance.

        <b>Expected results:</b>
        Information about specific configmap.

        <b>Steps:</b>
        - Get information about specific configmap.
        - Verify if information contains configmap name.
        """
        step("Get specific configmap")
        response = ContainerBrokerInstance.get_configmap(configmap_name="minio")
        assert response is not None
        assert response["metadata"]["labels"]["app"] == "minio"

    def test_get_non_existing_configmap(self):
        """
        <b>Description:</b>
        Get non existing configmap.

        <b>Input data:</b>
        Container broker instance.

        <b>Expected results:</b>
        It is not possible to get non existing configmap.

        <b>Steps:</b>
        - Get information about configmap.
        - Verify that HTTP response status code is 404 with proper message.
        """
        step("Try to get non existing configmap")
        expected_msg = ContainerBrokerHttpStatus.MSG_CONFIGMAPS_NOT_FOUND.format(self.INVALID_PARAM)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                ContainerBrokerInstance.get_configmap,
                                                configmap_name=self.INVALID_PARAM)

    def test_get_specific_secret(self):
        """
        <b>Description:</b>
        Get specific secret.

        <b>Input data:</b>
        Container broker instance.

        <b>Expected results:</b>
        Information about specific secret.

        <b>Steps:</b>
        - Get information about specific secret.
        - Verify if information contains secret name.
        """
        step("Get specific secret")
        response = ContainerBrokerInstance.get_secret(secret_name="minio")
        assert response is not None
        assert response["metadata"]["name"] == "minio"

    def test_get_non_existing_secret(self):
        """
        <b>Description:</b>
        Get non existing secret.

        <b>Input data:</b>
        Container broker instance.

        <b>Expected results:</b>
        It is not possible to get non existing secret.

        <b>Steps:</b>
        - Get information about secret.
        - Verify that HTTP response status code is 404 with proper message.
        """
        step("Try to get non existing secret")
        expected_msg = ContainerBrokerHttpStatus.MSG_SECRET_NOT_FOUND.format(self.INVALID_PARAM)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                ContainerBrokerInstance.get_secret, secret_name=self.INVALID_PARAM)

    def test_expose_unexpose_service(self, catalog_instance_nats):
        """
        <b>Description:</b>
        Expose and unexpose service instance

        <b>Input data:</b>
        - Container broker instance
        - Hostname
        - Port

        <b>Expected results:</b>
        It is possible to expose and unexpose service instance.

        <b>Steps:</b>
        - Verify hosts number of unexposed service instance.
        - Expose service instance.
        - Send request to exposed service instance.
        - Try to expose service instance again.
        - Verify that HTTP response status code is 409 with proper message.
        - Unexpose service instance.
        - Try to unexpose instance once again
        - Verify that HTTP response status code is 404 with proper message.
        """
        step("Verify hosts number of unexposed service instance")
        nats_instance = ContainerBrokerInstance(instance_id=catalog_instance_nats.id)
        hosts = nats_instance.get_hosts()
        assert len(hosts) == 0
        step("Expose service instance")
        nats_instance.expose_service_instance(hostname=self.HOSTNAME, ports=[self.PORT])
        hosts = nats_instance.get_hosts()
        expected_host = "http://{}-{}.{}".format(self.HOSTNAME, self.PORT, config.tap_domain)
        assert expected_host in hosts
        step("Send request to exposed service instance")
        response = self._send_request(url=expected_host)
        assert str(self.PORT) in str(response.text)
        step("Try to expose service instance again")
        expected_msg = ContainerBrokerHttpStatus.MSG_INGRESS_ALREADY_EXISTS.format(catalog_instance_nats.id)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_CONFLICT, expected_msg,
                                                nats_instance.expose_service_instance,
                                                hostname=self.HOSTNAME, ports=[self.PORT])
        step("Unexpose service instance")
        nats_instance.unexpose_service_instance()
        hosts = nats_instance.get_hosts()
        assert len(hosts) == 0
        step("Try to unexpose instance once again")
        expected_msg = ContainerBrokerHttpStatus.MSG_INGRESS_NOT_FOUND.format(catalog_instance_nats.id)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                nats_instance.unexpose_service_instance)

    def test_unexpose_service_with_invalid_service_id(self):
        """
        <b>Description:</b>
        Try to unexpose service instance with invalid service id

        <b>Input data:</b>
        - Container broker instance.
        - Invalid instance id.

        <b>Expected results:</b>
        It is not possible to unexpose service with invalid instance id.

        <b>Steps:</b>
        - Try to unexpose service instance.
        - Verify that HTTP response status code is 404 with proper message.
        """
        step("Try to unexpose service instance with invalid service id")
        expected_msg = ContainerBrokerHttpStatus.MSG_INGRESS_KEY_NOT_FOUND.format(self.INVALID_PARAM,
                                                                                  self.INVALID_PARAM)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                ContainerBrokerInstance.unexpose_service_with_instance_id,
                                                instance_id=self.INVALID_PARAM)

    def test_expose_service_invalid_port(self, catalog_instance_nats):
        """
        <b>Description:</b>
        Try to expose service instance with invalid port

        <b>Input data:</b>
        - Container broker instance.
        - Hostname
        - Invalid port.

        <b>Expected results:</b>
        It is not possible to expose service with invalid port.

        <b>Steps:</b>
        - Try to expose service instance.
        - Verify that HTTP response status code is 500 with proper message.
        """
        nats_instance = ContainerBrokerInstance(instance_id=catalog_instance_nats.id)
        step("Try to expose service instance with invalid port")
        expected_msg = ContainerBrokerHttpStatus.MSG_CANNOT_EXPOSE.format(catalog_instance_nats.id, self.INVALID_PORT)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_INTERNAL_SERVER_ERROR, expected_msg,
                                                nats_instance.expose_service_instance, hostname=self.HOSTNAME,
                                                ports=[self.INVALID_PORT])

    def test_expose_service_without_hostname(self, catalog_instance_nats):
        """
        <b>Description:</b>
        Try to expose service instance without hostname

        <b>Input data:</b>
        - Container broker instance.
        - Port.

        <b>Expected results:</b>
        It is not possible to expose service without hostname.

        <b>Steps:</b>
        - Try to expose service instance.
        - Verify that HTTP response status code is 400 with proper message.
        """
        nats_instance = ContainerBrokerInstance(instance_id=catalog_instance_nats.id)
        body = {"ports": [self.PORT]}
        step("Try to expose service instance without hostname")
        expected_msg = ContainerBrokerHttpStatus.MSG_EMPTY_HOSTNAME.format(catalog_instance_nats.id,
                                                                           "-{}.{}".format(self.PORT,
                                                                                           config.tap_domain))
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_BAD_REQUEST, expected_msg,
                                                nats_instance.expose_service_instance, hostname=None, ports=None,
                                                body=body)

    def test_get_custom_configmap_secret(self, open_tunnel, catalog_instance_nats):
        """
        <b>Description:</b>
        Get custom configmap and secret.

        <b>Input data:</b>
        - Container broker service instance

        <b>Expected results:</b>
        It is possible to get cucstom configmap and secret.

        <b>Steps:</b>
        - Get custom configmap name.
        - Get custom configmap details.
        - Get custom secret name.
        - Get custom secret details.
        - Delete service instance.
        - Verify if custom configmap exists - HTTP response status code is 404 with proper message.
        - Verify if custom secret exists - HTTP response status code is 404 with proper message
        """
        step("Get custom configmap name")
        configmap_name_suffix = "-nats-credentials"
        configmap_name = self._get_configmap(open_tunnel, configmap_name_suffix)
        step("Get custom configmap details")
        response = ContainerBrokerInstance.get_configmap(configmap_name=configmap_name)
        assert configmap_name == response["metadata"]["name"]
        assert response["metadata"]["labels"]["instance_id"] == catalog_instance_nats.id

        step("Get custom secret name")
        secret_name_suffix = "-nats-credentials"
        secret_name = self._get_secret(open_tunnel, secret_name_suffix)
        step("Get custom secret details")
        response = ContainerBrokerInstance.get_secret(secret_name=secret_name)
        assert secret_name == response["metadata"]["name"]
        assert response["metadata"]["labels"]["instance_id"] == catalog_instance_nats.id

        step("Delete service instance")
        catalog_instance_nats.stop()
        catalog_instance_nats.cleanup()
        step("Verify if custom configmap exists")
        expected_msg = ContainerBrokerHttpStatus.MSG_CONFIGMAPS_NOT_FOUND.format(configmap_name)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                ContainerBrokerInstance.get_configmap, configmap_name=configmap_name)
        step("Verify if custom secret exists")
        expected_msg = ContainerBrokerHttpStatus.MSG_SECRET_NOT_FOUND.format(secret_name)
        assertions.assert_raises_http_exception(ContainerBrokerHttpStatus.CODE_NOT_FOUND, expected_msg,
                                                ContainerBrokerInstance.get_secret, secret_name=secret_name)
