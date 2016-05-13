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

from configuration.config import CONFIG
from modules.constants import TapComponent as TAP, Urls
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, incremental, priority
from modules.service_tools.arcadia import Arcadia
from modules.tap_object_model import DataSet
from modules.tap_object_model.flows import data_catalog
from tests.fixtures.test_data import TestData


logged_components = (TAP.dataset_publisher, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [components.dataset_publisher, components.das, components.hdfs_downloader, components.metadata_parser]


@incremental
@priority.high
@pytest.mark.skipif(CONFIG["kerberos"], reason="Not enabled on kerberos environment")
class ArcadiaTest(TapTestCase):
    arcadia = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_transfer(cls, request, test_org, add_admin_to_test_org):
        cls.transfer, cls.dataset = data_catalog.create_dataset_from_link(org=test_org, source=Urls.test_transfer_link)

        def fin():
            cls.dataset.api_delete()
            cls.transfer.api_delete()
        request.addfinalizer(fin)

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def get_arcadia(cls, request):
        cls.step("Get arcadia dataconnection")
        cls.arcadia = Arcadia()

        def fin():
            cls.arcadia.teardown_test_datasets()
        request.addfinalizer(fin)

    @pytest.mark.skip("DPNG-7197 Arcadia test fails - mismatch of expected database name")
    def test_0_create_new_dataset_and_import_it_to_arcadia(self):
        self.step("Publish created dataset")
        self.dataset.api_publish()
        self.step("Check that organization name is visible on the database list in arcadia")
        db_list = self.arcadia.get_database_list()
        self.assertIn(TestData.test_org.name, db_list, "Organization not found in database list in arcadia")
        self.step("Check that dataset name is visible on the table list in arcadia")
        table_list = self.arcadia.get_table_list(TestData.test_org.name)
        self.assertIn(self.dataset.title, table_list, "Dataset not found in table list in arcadia")
        self.step("Create new dataset in arcadia")
        arcadia_dataset = self.arcadia.create_dataset(TestData.test_org.name, self.dataset.title)
        self.assertInWithRetry(arcadia_dataset, self.arcadia.get_dataset_list)

    @pytest.mark.skip("DPNG-7197 Arcadia test fails - mismatch of expected database name")
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
