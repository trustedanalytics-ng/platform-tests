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
from modules.app_sources import AppSources
from modules.constants import ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP, ServiceLabels, ServicePlan,\
    TapGitHub, Urls
from modules.file_utils import get_link_content
from modules.http_client.configuration_provider.cloud_foundry import CloudFoundryConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.client_auth.http_method import HttpMethod
from modules.markers import components, priority, incremental
from modules.tap_logger import step
from modules.tap_object_model import Application, Upsi, ServiceInstance
from modules.tap_object_model.flows.data_catalog import create_dataset_from_link
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.hive_broker,)
pytestmark = [components.hive_broker]


@incremental
@priority.medium
@pytest.mark.skipif(not config.kerberos, reason="No point to run without kerberos")
class TestHive:
    SSO_INSTANCE_NAME = "sso"
    TABLE_NAME = "table1"
    COLUMN_NAME = "col_col0"
    hdfs_reader_app = None
    hive_client = None

    @pytest.fixture(scope="class")
    def hdfs_instance(self, request, test_org, test_space):
        step("Create hdfs instance")
        instance = ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.HDFS,
            name=generate_test_object_name(),
            service_plan_name=ServicePlan.SHARED
        )
        request.addfinalizer(instance.cleanup)
        return instance

    @pytest.fixture(scope="class")
    def kerberos_instance(self, request, test_org, test_space):
        step("Create kerberos instance")
        instance = ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.KERBEROS,
            name=generate_test_object_name(),
            service_plan_name=ServicePlan.SHARED
        )
        request.addfinalizer(instance.cleanup)
        return instance

    @pytest.fixture(scope="class")
    def hive_instance(self, request, test_org, test_space):
        step("Create hive instance")
        instance = ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.HIVE,
            name=generate_test_object_name(),
            service_plan_name=ServicePlan.SHARED
        )
        request.addfinalizer(instance.cleanup)
        return instance

    @pytest.fixture(scope="class")
    def cups_sso_instance(self, request, test_space):
        step("Create sso instance")
        token = {"tokenKey": "{}/token_key".format(config.uaa_url)}
        instance = Upsi.cf_api_create(
            name=self.SSO_INSTANCE_NAME,
            space_guid=test_space.guid,
            credentials=token
        )
        request.addfinalizer(instance.cleanup)
        return instance

    @pytest.fixture(scope="class")
    def dataset_target_uri(self, test_org, test_space, class_context, add_admin_to_test_org, add_admin_to_test_space):
        _, dataset = create_dataset_from_link(class_context, test_org, Urls.test_transfer_link)
        return dataset.target_uri

    @pytest.fixture(scope="class")
    def expected_transfer_content(self):
        expected_transfer = get_link_content(Urls.test_transfer_link)
        expected_transfer = [i.split(",") for i in expected_transfer.split("\n") if i]
        return expected_transfer

    def test_0_push_hdfs_hive_demo(self, test_space, dataset_target_uri, hdfs_instance, kerberos_instance,
                                   hive_instance, cups_sso_instance, login_to_cf, class_context):
        step("Get app sources")
        repo = AppSources.from_github(repo_name=TapGitHub.hdfs_hive_demo, repo_owner=TapGitHub.intel_data,
                                      gh_auth=config.github_credentials())
        repo.compile_mvn()
        step("Push hdfs-hive-demo app to cf")
        self.__class__.hdfs_reader_app = Application.push(class_context, space_guid=test_space.guid,
                                                          source_directory=repo.path,
                                                          bound_services=(hdfs_instance.name, kerberos_instance.name,
                                                                          hive_instance.name, cups_sso_instance.name))
        step("Check hdfs-hive-demo app has url")
        assert len(self.hdfs_reader_app.urls) == 1

    def test_1_create_and_get_table_content(self, dataset_target_uri, expected_transfer_content):
        self.__class__.hive_client = HttpClientFactory.get(
            CloudFoundryConfigurationProvider.get(url="http://{}/rest/hive".format(self.hdfs_reader_app.urls[0])))
        dir_path = dataset_target_uri[:dataset_target_uri.rfind("/")]
        step("Create hive table with csv data")
        self.hive_client.request(method=HttpMethod.POST, path=self.TABLE_NAME,
                                 params={"fullHdfsDirPath": dir_path, "headerFilePath": dataset_target_uri})

        step("Get hive table content")
        hive_table_content = self.hive_client.request(method=HttpMethod.GET, path=self.TABLE_NAME)
        hive_table_content = [i.strip().split(" ") for i in hive_table_content.split("\n") if i]
        step("Check both are the same")
        assert hive_table_content == expected_transfer_content

    def test_2_get_table_column_content(self, expected_transfer_content):
        step("Get hive table column content")
        path = "{}/{}".format(self.TABLE_NAME, self.COLUMN_NAME)
        hive_table_column_content = self.hive_client.request(method=HttpMethod.GET, path=path)
        hive_table_column_content = [i.strip() for i in hive_table_column_content.split("\n") if i]
        step("Check both columns are the same")
        expected_column_0 = [i[0] for i in expected_transfer_content]
        assert hive_table_column_content == expected_column_0

    def test_3_delete_table(self, test_org, test_space):
        self.hive_client.request(method=HttpMethod.DELETE, path=self.TABLE_NAME)
        assert_raises_http_exception(HttpStatus.CODE_INTERNAL_SERVER_ERROR, HttpStatus.MSG_INTERNAL_SERVER_ERROR,
                                     self.hive_client.request, method=HttpMethod.GET, path=self.TABLE_NAME)
