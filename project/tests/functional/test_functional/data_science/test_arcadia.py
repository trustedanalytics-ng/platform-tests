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

from modules.constants import Priority, TapComponent as TAP, Urls
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, incremental
from modules.service_tools.arcadia import Arcadia
from modules.tap_object_model import DataSet, Organization, Space, Transfer, User
from tests.fixtures import teardown_fixtures


@log_components()
@incremental(Priority.high)
@components(TAP.dataset_publisher, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class ArcadiaTest(TapTestCase):
    arcadia = None

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Create test organization and test spaces")
        cls.test_org = Organization.api_create()
        cls.test_space = Space.api_create(cls.test_org)
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.test_org.guid)
        cls.step("Create non admin user")
        cls.non_admin_client = User.api_create_by_adding_to_space(cls.test_org.guid, cls.test_space.guid).login()
        cls.step("Create new transfer")
        cls.transfer = Transfer.api_create(org_guid=cls.test_org.guid, source=Urls.test_transfer_link)
        cls.dataset = DataSet.api_get_matching_to_transfer(org=cls.test_org, transfer_title=cls.transfer.title)
        cls.step("Get arcadia dataconnection")
        cls.arcadia = Arcadia()

    @classmethod
    def tearDownClass(cls):
        cls.arcadia.teardown_test_datasets()
        super().tearDownClass()

    def test_0_create_new_dataset_and_import_it_to_arcadia(self):
        self.step("Publish created dataset")
        self.dataset.api_publish()
        self.step("Check that organization name is visible on the database list in arcadia")
        db_list = self.arcadia.get_database_list()
        self.assertIn(self.test_org.name, db_list, "Organization not found in database list in arcadia")
        self.step("Check that dataset name is visible on the table list in arcadia")
        table_list = self.arcadia.get_table_list(self.test_org.name)
        self.assertIn(self.dataset.title, table_list, "Dataset not found in table list in arcadia")
        self.step("Create new dataset in arcadia")
        arcadia_dataset = self.arcadia.create_dataset(self.test_org.name, self.dataset.title)
        self.assertInWithRetry(arcadia_dataset, self.arcadia.get_dataset_list)

    def test_1_change_dataset_to_public_and_import_it_to_arcadia(self):
        self.step("Change dataset to public")
        self.dataset.api_update(is_public=True)
        self.dataset = DataSet.api_get(self.dataset.id)
        self.assertTrue(self.dataset.is_public, "Dataset was not updated")
        self.step("Publish updated dataset")
        self.dataset.api_publish()
        self.step("Check that dataset name is visible on the public table list in arcadia")
        table_list = self.arcadia.get_table_list("public")
        self.assertIn(self.dataset.title, table_list, "Dataset not found in table list in arcadia")
        self.step("Create new dataset in arcadia")
        arcadia_dataset = self.arcadia.create_dataset("public", self.dataset.title)
        self.assertInWithRetry(arcadia_dataset, self.arcadia.get_dataset_list)
