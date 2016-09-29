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

from modules.constants import HttpStatus, TapComponent as TAP, Urls
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet
from modules.tap_object_model.flows import data_catalog
from tests.fixtures import assertions

logged_components = (TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)]


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class TestUpdateDeleteDataSet:

    @retry(AssertionError, tries=10, delay=3)
    def _assert_updated(self, data_set_id, updated_attribute_name, expected_value):
        updated_dataset = DataSet.api_get(data_set_id)
        updated_value = getattr(updated_dataset, updated_attribute_name)
        assert updated_value == expected_value, "Data set was not updated"

    @pytest.fixture(scope="function")
    def dataset(self, test_org, context):
        step("Create data set")
        _, dataset = data_catalog.create_dataset_from_link(context, org_guid=test_org.guid,
                                                           source=Urls.test_transfer_link)
        return dataset

    @priority.high
    def test_delete_dataset(self, test_org, dataset):
        step("Delete the data set")
        dataset.api_delete()
        step("Get data set list and check the deleted one is not on it")
        datasets = DataSet.api_get_list(org_guid_list=[test_org.guid])
        assert dataset not in datasets

    @priority.low
    def test_cannot_delete_data_set_twice(self, dataset):
        step("Delete data set")
        dataset.api_delete()
        step("Try to delete the dataset again")
        assertions.assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY, dataset.api_delete)

    @priority.medium
    @pytest.mark.public_dataset
    def test_change_private_to_public_to_private(self, dataset):
        step("Update data set from private to public")
        dataset.api_update(is_public=True)
        step("Check that private data set was changed to public")
        self._assert_updated(dataset.id, "is_public", True)
        step("Update data set from public to private")
        dataset.api_update(is_public=False)
        step("Check that public data set was changed to private")
        self._assert_updated(dataset.id, "is_public", False)

    @priority.low
    def test_update_data_set_category(self, dataset):
        new_category = next(c for c in DataSet.CATEGORIES if c != dataset.category)
        step("Update data set, change category")
        dataset.api_update(category=new_category)
        self._assert_updated(dataset.id, "category", new_category)

    @priority.low
    def test_update_dataset_to_non_existing_category(self, dataset):
        new_category = "user_category"
        step("Update data set with new category")
        dataset.api_update(category=new_category)
        self._assert_updated(dataset.id, "category", new_category)
