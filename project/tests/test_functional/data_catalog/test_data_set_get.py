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

from modules.constants import TapComponent as TAP, Urls
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Transfer

logged_components = (TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)]


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class TestGetDataSets(object):

    data_sample = ["COL_0", "COL_1", "COL_2", "COL_3", "COL_4", "COL_5", "COL_6", "COL_7"]
    TEST_FILE_URL = Urls.test_transfer_link

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_test_data_sets(cls, request, test_org, class_context):
        step("Create new transfer for each category")
        cls.transfers = []
        for category in DataSet.CATEGORIES:
            cls.transfers.append(Transfer.api_create(class_context, category, is_public=False, org_guid=test_org.guid,
                                                     source=cls.TEST_FILE_URL))
        for category in DataSet.CATEGORIES:
            cls.transfers.append(Transfer.api_create(class_context, category, is_public=True, org_guid=test_org.guid,
                                                     source=cls.TEST_FILE_URL))
        step("Ensure that transfers are finished")
        for transfer in cls.transfers:
            transfer.ensure_finished()
        step("Get all data sets in the test org")
        cls.transfer_titles = [t.title for t in cls.transfers]
        dataset_list = DataSet.api_get_list(org_guid_list=[test_org.guid])
        cls.datasets = [d for d in dataset_list if d.title in cls.transfer_titles]

    def _filter_datasets(self, org, filters=(), only_private=False, only_public=False, query=""):
        ds_list = DataSet.api_get_list(org_guid_list=[org.guid], query=query, filters=filters,
                                       only_private=only_private, only_public=only_public)
        return [d for d in ds_list if d in self.datasets]

    @priority.high
    def test_match_dataset_to_transfer(self):
        step("Check if a data set was created for each transfer")
        missing_ds = []
        dataset_titles = [ds.title for ds in self.datasets]
        for tr in self.transfers:
            if tr.title not in dataset_titles:
                missing_ds.append(tr.title)
        assert missing_ds == [], "Missing datasets: {}".format(missing_ds)

    @priority.medium
    @pytest.mark.parametrize("category", DataSet.CATEGORIES)
    def test_get_datasets_by_category(self, category, test_org):
        step("Retrieve datasets by categories")
        filtered_datasets = self._filter_datasets(test_org, ({"category": [category]},))
        expected_datasets = [d for d in self.datasets if d.category == category]
        assert filtered_datasets == expected_datasets

    @priority.medium
    def test_get_datasets_by_creation_date(self, test_org):
        step("Sort datasets by creation time and retrieve first two")
        time_range = sorted([dataset.creation_time for dataset in self.datasets][:2])
        step("Retrieve datasets for specified time range")
        filtered_datasets = self._filter_datasets(test_org, ({"creationTime": time_range},))
        expected_datasets = [d for d in self.datasets if time_range[0] <= d.creation_time <= time_range[1]]
        assert sorted(filtered_datasets) == sorted(expected_datasets)

    @priority.medium
    @pytest.mark.parametrize("file_format", DataSet.FILE_FORMATS)
    def test_get_datasets_by_file_format(self, file_format, test_org):
        # Test should be updated when we will receive answer about supported file formats.
        step("Retrieve datasets by file format")
        filtered_datasets = self._filter_datasets(test_org, ({"format": [file_format]},))
        expected_datasets = [d for d in self.datasets if d.format == file_format]
        assert sorted(filtered_datasets) == sorted(expected_datasets)

    @priority.medium
    @pytest.mark.public_dataset
    def test_get_public_datasets_from_current_org(self, test_org):
        step("Retrieve only public datasets")
        filtered_datasets = self._filter_datasets(test_org, only_public=True)
        expected_datasets = [d for d in self.datasets if d.is_public]
        assert sorted(filtered_datasets) == sorted(expected_datasets)

    @priority.medium
    def test_get_private_datasets_from_current_org(self, test_org):
        step("Retrieve only private datasets")
        filtered_datasets = self._filter_datasets(test_org, only_private=True)
        expected_datasets = [d for d in self.datasets if not d.is_public]
        assert sorted(filtered_datasets) == sorted(expected_datasets)

    @priority.medium
    def test_compare_dataset_details_with_transfer_details(self):
        step("Get transfer and matching dataset")
        transfer = self.transfers[0]
        dataset = next(iter([ds for ds in self.datasets if ds.title == transfer.title]), None)
        step("Check that dataset exists for chosen transfer")
        assert dataset is not None, "Dataset doesn't exist for transfer {}".format(transfer)
        step("Check dataset and transfer category")
        assert dataset.category == transfer.category
        step("Check dataset and transfer org guid")
        assert dataset.org_guid == transfer.organization_guid
        step("Check dataset and transfer file format")
        assert dataset.format == "CSV"
        step("Check dataset and transfer public status")
        assert dataset.is_public == transfer.is_public
        step("Check dataset and transfer source uri")
        assert dataset.source_uri == transfer.source

    @priority.medium
    def test_get_datasets_by_keyword_title(self, test_org):
        title = self.transfer_titles[0]
        step("Retrieve datasets by title keyword")
        filtered_datasets = self._filter_datasets(test_org, query=title)
        expected_datasets = [d for d in self.datasets if d.title == title]
        assert sorted(filtered_datasets) == sorted(expected_datasets)

    @priority.medium
    def test_get_datasets_by_keyword_source_uri(self, test_org):
        step("Retrieve datasets by source uri keyword")
        filtered_datasets = self._filter_datasets(test_org, query=self.TEST_FILE_URL)
        assert sorted(filtered_datasets) == sorted(self.datasets)

    @priority.medium
    @pytest.mark.parametrize("data_sample", data_sample)
    def test_get_datasets_by_keyword_data_sample(self, data_sample, test_org):
        step("Retrieve datasets by data sample keyword")
        filtered_datasets = self._filter_datasets(test_org, query=data_sample)
        assert sorted(filtered_datasets) == sorted(self.datasets)
