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
from modules.constants import TapComponent as TAP, Urls
from modules.file_utils import generate_csv_file
from modules.markers import incremental, priority
from modules.tap_object_model import Organization, ServiceInstance, User
from modules.tap_object_model.flows.data_catalog import create_dataset_from_file, create_dataset_from_link
from modules.tap_logger import step
from modules.webhdfs_tools import WebhdfsTools

logged_components = (TAP.auth_gateway, TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser,
                     TAP.hdfs_uploader, TAP.user_management)
pytestmark = [pytest.mark.components(TAP.auth_gateway)]


@pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 (multiple organizations). Tests should use test application for "
                         "checking user permissions on cdh")
@incremental
@priority.medium
@pytest.mark.skipif(config.kerberos, reason="DPNG-8628 WebHDFS needs to be workable on environments with kerberos")
class TestAuthGateway:
    HDFS_INSTANCE_NAME = "hdfs-instance"
    REQUIRED_SUB_DIRS = ["apps", "brokers", "tmp", "user"]
    HBASE_PATH = "hbase/data"
    USER_PATH = "org/{}/user"
    USERSPACE_PATH = "org/{}/brokers/userspace/{}"
    dataset = None
    test_org = None
    test_org_manager = None
    test_org_manager_client = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_web_hdfs_client(cls, request):
        raise NotImplementedError("Will be refactored in DPNG-8898.")
        ssh_tunel = SshTunnel(config.cdh_master_0_hostname, WebhdfsTools.VIA_HOST_USERNAME,
                              path_to_key=WebhdfsTools.PATH_TO_KEY, port=WebhdfsTools.DEFAULT_PORT, via_port=22,
                              via_hostname=config.jumpbox_hostname, local_port=WebhdfsTools.DEFAULT_PORT)
        ssh_tunel.connect()
        cls.webhdfs_client = WebhdfsTools.create_client(host="localhost")
        cls.hdfs = WebhdfsTools()
        request.addfinalizer(ssh_tunel.disconnect)

    @pytest.fixture(scope="class")
    def core_hdfs_instance(self, core_space):
        service_instances = ServiceInstance.api_get_list(core_space.guid)
        hdfs_instance = next((s for s in service_instances if s.name == self.HDFS_INSTANCE_NAME), None)
        assert hdfs_instance is not None, "{} not found in core space".format(self.HDFS_INSTANCE_NAME)
        return hdfs_instance

    @staticmethod
    def _assert_directory_in_hdfs(hdfs_dirs, name, owner, group):
        step("Check that directory {} was correctly created in hdfs".format(name))
        hdfs_org_directory = next((d for d in hdfs_dirs if d["pathSuffix"] == name), None)
        assert hdfs_org_directory is not None
        assert hdfs_org_directory["owner"] == owner
        assert hdfs_org_directory["group"] == group

    def _list_hdfs_directories(self, path):
        return self.hdfs.list_directory(self.webhdfs_client, path)["FileStatuses"]["FileStatus"]

    def _assert_directory_contains_subdirectories(self, name):
        step("Check that org directory contains required directories")
        hdfs_sub_dirs = self._get_hbase_namespaces("org/{}".format(name))
        not_found_sub_dirs = [d for d in self.REQUIRED_SUB_DIRS if d not in hdfs_sub_dirs]
        assert not_found_sub_dirs == [], "Organization directory doesn't contain subdirectories"

    def _get_hbase_namespaces(self, path):
        hbase_hdfs_dirs = self._list_hdfs_directories(path)
        return [hdfs_dir["pathSuffix"] for hdfs_dir in hbase_hdfs_dirs]

    def test_0_check_hdfs_directory_is_created_for_new_org(self, class_context):
        step("Create test organization")
        self.__class__.test_org = Organization.api_create(class_context)
        hdfs_dirs = self._list_hdfs_directories("org")
        self._assert_directory_in_hdfs(hdfs_dirs, name=self.test_org.guid, owner="{}_admin".format(self.test_org.guid),
                                       group=self.test_org.guid)
        self._assert_directory_contains_subdirectories(name=self.test_org.guid)
        step("Check that organization namespace was created in hbase")
        org_namespace = self.test_org.guid.replace("-", "")
        assert org_namespace in self._get_hbase_namespaces(self.HBASE_PATH), "Organization namespace was not found"

    def test_1_check_created_user(self, class_context):
        step("Create test organization manager")
        self.__class__.test_org_manager = User.api_create_by_adding_to_organization(class_context, self.test_org.guid)
        self.__class__.test_org_manager_client = self.test_org_manager.login()
        step("Check user is in test organization")
        org_hdfs_user_dirs = self._list_hdfs_directories(self.USER_PATH.format(self.test_org.guid))
        self._assert_directory_in_hdfs(org_hdfs_user_dirs, name=self.test_org_manager.guid,
                                       owner=self.test_org_manager.guid, group=self.test_org.guid)

    def test_2_create_dataset(self, class_context, core_hdfs_instance):
        step("Create dataset from url")
        _, self.__class__.dataset = create_dataset_from_link(class_context, self.test_org.guid, Urls.test_transfer_link,
                                                             client=self.test_org_manager_client)
        step("Check dataset directory in hdfs")
        hdfs_dirs = self._list_hdfs_directories(self.USERSPACE_PATH.format(self.test_org.guid, core_hdfs_instance.guid))
        self._assert_directory_in_hdfs(hdfs_dirs, name=self.dataset.object_store_id, owner=self.test_org_manager.guid,
                                       group=self.test_org.guid)

    def test_3_upload_dataset(self, class_context, core_hdfs_instance):
        step("Create dataset from uploaded file")
        _, self.__class__.dataset = create_dataset_from_file(class_context, self.test_org.guid, generate_csv_file(),
                                                             client=self.test_org_manager_client)
        step("Check dataset directory in hdfs")
        hdfs_dirs = self._list_hdfs_directories(self.USERSPACE_PATH.format(self.test_org.guid, core_hdfs_instance.guid))
        self._assert_directory_in_hdfs(hdfs_dirs, name=self.dataset.object_store_id, owner=self.test_org_manager.guid,
                                       group=self.test_org.guid)

    @pytest.mark.bugs("DPNG-8734 Dataset file on hdfs is not deleted after dataset deletion in data directory")
    def test_4_delete_dataset(self, core_hdfs_instance):
        step("Delete dataset")
        self.dataset.api_delete()
        step("Check that dataset hdfs path has been deleted")
        hdfs_dirs = self._get_hbase_namespaces(self.USERSPACE_PATH.format(self.test_org.guid, core_hdfs_instance.guid))
        assert self.dataset.object_store_id not in hdfs_dirs, "Dataset directory has not been deleted"

    @pytest.mark.skip(reason="Only single organization for 0.8 scope")
    def test_5_delete_org(self):
        step("Delete organization")
        self.test_org.api_delete()
        step("Check that hdfs organization path has been deleted")
        hdfs_dirs = self._get_hbase_namespaces("org")
        assert self.test_org.guid not in hdfs_dirs, "Organization directory has not been deleted"
        step("Check that organization namespace was deleted from hbase")
        org_namespace = self.test_org.guid.replace("-", "")
        namespaces = self._get_hbase_namespaces(self.HBASE_PATH)
        assert org_namespace not in namespaces, "Organization namespace was not deleted"