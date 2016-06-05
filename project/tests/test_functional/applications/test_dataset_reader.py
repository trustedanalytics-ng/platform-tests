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

import json

import pytest
import requests

from modules.app_sources import AppSources
from modules.constants import ServiceLabels, ServicePlan, TapComponent as TAP, TapGitHub, Urls
from modules.markers import priority, components, incremental
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, Transfer, DataSet, User, ServiceBinding

logged_components = (TAP.service_catalog, TAP.das)
pytestmark = [components.dataset_reader]


@incremental
@priority.medium
class TestDatasetReader:

    HDFS_INSTANCE_NAME = "hdfs-instance"
    KERBEROS_INSTANCE_NAME = "kerberos-instance"
    hdfs_reader_app = None

    @pytest.fixture(scope="class")
    def hdfs_instance(self, request, test_org, test_space):
        step("Create hdfs instance")
        instance = ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.HDFS,
            name=self.HDFS_INSTANCE_NAME,
            service_plan_name=ServicePlan.SHARED
        )
        request.addfinalizer(lambda: instance.cleanup())
        return instance

    @pytest.fixture(scope="class")
    def kerberos_instance(self, request, test_org, test_space):
        step("Create kerberos instance")
        instance = ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.KERBEROS,
            name=self.KERBEROS_INSTANCE_NAME,
            service_plan_name=ServicePlan.SHARED
        )
        request.addfinalizer(lambda: instance.cleanup())
        return instance

    @pytest.fixture(scope="class")
    def dataset_target_uri(self, test_org, test_space, class_context, admin_user):
        step("Add admin to space with developer role")
        admin_user.api_add_to_space(test_space.guid, test_org.guid, User.SPACE_ROLES["developer"])
        step("Create transfer")
        transfer = Transfer.api_create(class_context, org_guid=test_org.guid, source=Urls.test_transfer_link)
        transfer.ensure_finished()
        step("Get dataset")
        dataset = DataSet.api_get_matching_to_transfer(transfer.title, test_org)
        return dataset.target_uri

    @pytest.fixture(scope="class", autouse=True)
    def cleanup(self, request, hdfs_instance, kerberos_instance):
        def fin():
            if self.hdfs_reader_app is not None:
                for binding in ServiceBinding.api_get_list(self.hdfs_reader_app.guid):
                    binding.api_delete()
        request.addfinalizer(fin)

    def _get_link_content(self, link):
        """ Return content under the link as a string. """
        r = requests.get(link)
        r.raise_for_status()
        return r.content.decode()

    def test_0_push_dataset_reader_app(self, test_space, dataset_target_uri, hdfs_instance, kerberos_instance,
                                       login_to_cf, class_context):
        step("Get app sources")
        repo = AppSources.from_github(repo_name=TapGitHub.dataset_reader_sample, repo_owner=TapGitHub.trustedanalytics)
        repo.compile_mvn()

        step("Push dataset-reader app to cf")
        self.__class__.hdfs_reader_app = Application.push(class_context, space_guid=test_space.guid,
                                                          source_directory=repo.path,
                                                          bound_services=(hdfs_instance.name, kerberos_instance.name),
                                                          env={"FILE": dataset_target_uri})
        step("Check dataset reader app has url")
        assert len(self.hdfs_reader_app.urls) == 1

    def test_1_check_dataset_is_correct(self):
        step("Get content of the csv file submitted as transfer")
        expected_transfer = self._get_link_content(Urls.test_transfer_link)
        expected_transfer = [i.split(",") for i in expected_transfer.split("\n") if i]

        step("Get content of the transfer from dataset reader app")
        reader_transfer = self._get_link_content("http://{}/rest/parsed-dataset".format(self.hdfs_reader_app.urls[0]))
        reader_transfer = json.loads(reader_transfer)

        step("Check both are the same")
        assert reader_transfer == expected_transfer
