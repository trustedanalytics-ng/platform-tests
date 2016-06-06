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
from modules.markers import components, incremental, priority
from modules.service_tools.arcadia import Arcadia
from modules.tap_logger import step
from modules.tap_object_model import DataSet
from modules.tap_object_model.flows import data_catalog
from tests.fixtures import assertions


logged_components = (TAP.dataset_publisher, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [components.dataset_publisher, components.das, components.hdfs_downloader, components.metadata_parser]


@incremental
@priority.high
@pytest.mark.skipif(CONFIG["kerberos"], reason="Not enabled on kerberos environment")
class TestArcadia:
    arcadia = None

    @classmethod
    @pytest.fixture(scope="class")
    def dataset(cls, request, test_org, add_admin_to_test_org, class_context):
        _, dataset = data_catalog.create_dataset_from_link(class_context, org=test_org, source=Urls.test_transfer_link)
        return dataset

    @classmethod
    @pytest.fixture(scope="class")
    def arcadia(cls, request):
        step("Get arcadia dataconnection")
        arcadia = Arcadia()
        request.addfinalizer(lambda: arcadia.teardown_test_datasets())
        return arcadia

    @pytest.mark.bugs("DPNG-7434 Published dataset appears in Arcadia with considerable delay")
    def test_0_create_new_dataset_and_import_it_to_arcadia(self, test_org, dataset, arcadia):
        step("Publish created dataset")
        dataset.api_publish()
        step("Check that organization guid is visible on the database list in arcadia")
        expected_db_name = DataSet.escape_string(test_org.guid)
        db_list = arcadia.get_database_list()
        assert expected_db_name in db_list, "{} was not found in db list".format(expected_db_name)
        step("Check that dataset name is visible on the table list in arcadia")
        assertions.assert_in_with_retry(DataSet.escape_string(dataset.title), arcadia.get_table_list, expected_db_name)
        step("Create new dataset in arcadia")
        arcadia_dataset = arcadia.create_dataset(test_org.name, dataset.title)
        assertions.assert_in_with_retry(arcadia_dataset, arcadia.get_dataset_list)

    @pytest.mark.public_dataset
    @pytest.mark.bugs("DPNG-7434 Published dataset appears in Arcadia with considerable delay")
    def test_1_change_dataset_to_public_and_import_it_to_arcadia(self, test_org, dataset, arcadia):
        step("Change dataset to public")
        dataset.api_update(is_public=True)
        dataset = DataSet.api_get(dataset.id)
        assert dataset.is_public, "Dataset was not updated"
        step("Publish updated dataset")
        dataset.api_publish()
        step("Check that dataset name is visible on the public table list in arcadia")
        table_list = arcadia.get_table_list("public")
        assert dataset.title in table_list, "Dataset not found in table list in arcadia"
        step("Create new dataset in arcadia")
        arcadia_dataset = arcadia.create_dataset("public", dataset.title)
        assertions.assert_in_with_retry(arcadia_dataset, arcadia.get_dataset_list)
