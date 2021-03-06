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
from retry import retry

import config
from modules.constants import ApplicationPath, ServiceLabels, ServicePlan, TapComponent as TAP
from modules.exceptions import CommandExecutionException
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.markers import priority, incremental
from modules.tap_logger import step
from modules.tap_object_model import Application, KubernetesCluster, ServiceInstance, ServiceOffering
from tests.fixtures import assertions


logged_components = (TAP.kubernetes_broker, TAP.demiurge, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.kubernetes_broker, TAP.demiurge)]


@pytest.mark.skip("DPNG-11951 [api-tests] Adjust test_mongodb_clustered to new TAP")
@incremental
@priority.medium
@pytest.mark.skipif(not config.kubernetes, reason="No point to run without kubernetes")
class TestMongoDbClustered:

    MONGODB_SERVICE_LABEL = ServiceLabels.MONGO_DB_30_MULTINODE
    mongodb_instance = None
    mongodb_instance_key = None
    mongodb_app = None
    TEST_COLLECTION_NAME = "TestCollection"
    TEST_DATA = {'a': 1, 'b': 2, 'c': 3}
    JSON_HEADERS = {
        "Accept": "application/json",
        "Content-Types": "application/json; charset=UTF-8"
    }

    def test_0_check_mongodb_in_marketplace(self, test_space):
        """
        <b>Description:</b>
        Check that mongodb offering is present in marketplace.

        <b>Input data:</b>
        No input data

        <b>Expected results:</b>
        Test passes if mongodb offering is present in marketplace.

        <b>Steps:</b>
        1. Get list of all service offerings from marketplace.
        2. Check that mongodb offering is present in retrieved list.
        """
        step("Check if mongodb clustered service is in marketplace")
        marketplace = ServiceOffering.get_list()
        mongodb = next((service for service in marketplace if service.label == self.MONGODB_SERVICE_LABEL), None)
        assert mongodb is not None, "{} not available".format(self.MONGODB_SERVICE_LABEL)

    def test_1_create_mongodb_clustered_instance(self, class_context, test_org, test_space):
        """
        <b>Description:</b>
        Check that mongodb instance can be created with plan clustered.

        <b>Input data:</b>
        1. Test organization.

        <b>Expected results:</b>
        Test passes if mongodb service instance is created.

        <b>Steps:</b>
        1. Create mongodb service instance with plan clustered.
        2. Check that created service instance is present in service instance list.
        """
        step("Create new mongodb clustered service")
        self.__class__.mongodb_instance = ServiceInstance.api_create_with_plan_name(
            context=class_context,
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=self.MONGODB_SERVICE_LABEL,
            service_plan_name=ServicePlan.CLUSTERED
        )
        self.mongodb_instance.ensure_created()
        step("Check that the mongodb clustered is on the instances list")
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        assert self.mongodb_instance in instances

    def test_2_create_mongodb_clustered_key(self, test_space):
        # This functionality changed in new TAP
        # step("Create a key for the mongodb instance")
        # self.__class__.mongodb_instance_key = ServiceKey.api_create(self.mongodb_instance.guid)
        # This functionality changed in new TAP
        # step("Check a key for the mongodb instance")
        # summary = ServiceInstance.api_get_keys(test_space.guid)
        # assert self.mongodb_instance_key in summary[self.mongodb_instance]
        pass

    def test_3_check_kubernetes_cluster(self, test_org):
        """
        <b>Description:</b>
        Check that kubernetes cluster was created.

        <b>Input data:</b>
        1. Test organization.

        <b>Expected results:</b>
        Test passes if kubernetes cluster was successfully created.

        <b>Steps:</b>
        1. Check that kubenretes cluster was created.
        """
        step("Check test organization guid is on the list of clusters")
        KubernetesCluster.demiurge_api_get(name=test_org.guid)

    @retry(CommandExecutionException, tries=10, delay=10)
    def test_4_push_app(self, class_context, test_space, login_to_cf):
        """
        <b>Description:</b>
        Push mongodb api application to the platform.

        <b>Input data:</b>
        1. Mongodb api application

        <b>Expected results:</b>
        Test passes if mongodb api can be successfully pushed to the platform.

        <b>Steps:</b>
        1. Push mongodb api application to the platform.
        """
        step("Push application to cf")
        self.__class__.mongodb_app = Application.push(context=class_context,
                                                      source_directory=ApplicationPath.MONGODB_API,
                                                      space_guid=test_space.guid,
                                                      bound_services=(self.mongodb_instance.name,))

    def test_5_check_app(self, test_space):
        """
        <b>Description:</b>
        Check that application was successfully pushed to the platform.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if mongodb api was successfully pushed to the platform.

        <b>Steps:</b>
        1. Check that mongodb api application is in state running.
        2. Check that application is on the application list.
        """
        step("Check the application is running")
        assertions.assert_equal_with_retry(True, self.mongodb_app.cf_api_app_is_running)
        step("Check that application is on the list")
        apps = Application.cf_api_get_list_by_space(test_space.guid)
        assert self.mongodb_app in apps

    def test_6_add_collection(self):
        """
        <b>Description:</b>
        Check that new collections and documents can be added.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if new collection can be created and populated with new documents.

        <b>Steps:</b>
        1. Create new collection.
        2. Add new documents to the created collection.
        3. Check that collection was created and contains added documents.
        """
        client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(url=self.mongodb_app.urls[0]))
        step("Create test collection")
        client.request(HttpMethod.POST, path="collections", headers=self.JSON_HEADERS,
                       body={"new_collection": self.TEST_COLLECTION_NAME})
        step("Add documents to test collection")
        client.request(HttpMethod.POST, path="collections/{}/documents".format(self.TEST_COLLECTION_NAME),
                       headers=self.JSON_HEADERS, body={"data": self.TEST_DATA})
        step("Check collection was created properly")
        document = client.request(HttpMethod.GET, path="collections/{}/documents".format(self.TEST_COLLECTION_NAME),
                                  headers=self.JSON_HEADERS)["rows"][0]
        assert all([x in document.items() for x in self.TEST_DATA.items()]),\
            "Document: {}, expected: {}".format(document, self.TEST_DATA)

    def test_7_delete_mongodb_clustered_key(self, test_space):
        # This functionality changed in new TAP
        # step("Delete mongodb clustered service key")
        # self.mongodb_instance_key.api_delete()
        # step("Check that key has been deleted")
        # summary = ServiceInstance.api_get_keys(test_space.guid)
        # assert self.mongodb_instance_key not in summary[self.mongodb_instance]
        pass

    def test_8_delete_app(self, test_space):
        """
        <b>Description:</b>
        Check that mongodb api application can be deleted.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if mongodb api application can be deleted successfully.

        <b>Steps:</b>
        1. Delete mongodb api application.
        2. Get application list.
        3. Check that mongodb api application is no longer present in application list.
        """
        step("Delete application")
        self.mongodb_app.api_delete()
        step("Check that application is not on the list")
        apps = Application.api_get_list(test_space.guid)
        assert self.mongodb_app not in apps

    def test_9_delete_mongodb_clustered_instance(self, test_space):
        """
        <b>Description:</b>
        Check that mongodb service instance can be deleted.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if mongodb service instance is deleted.

        <b>Steps:</b>
        1. Delete mongodb service instance.
        2. Get service instances list.
        3. Check that mongodb service instance is no longer present in service instances list.
        """
        step("Delete mongodb clustered service")
        self.mongodb_instance.api_delete()
        step("Check that the mongodb clustered is not on the instances list")
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        assert self.mongodb_instance not in instances
