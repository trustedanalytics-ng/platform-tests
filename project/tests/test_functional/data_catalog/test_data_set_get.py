#
# Copyright (c) 2015-2016 Intel Corporation
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
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.tap_object_model import DataSet, Organization, Transfer
from tests.fixtures import test_data


logged_components = (TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [components.data_catalog, components.das, components.hdfs_downloader, components.metadata_parser]


class GetDataSets(TapTestCase):

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_test_data_sets(cls, request, test_org, add_admin_to_test_org, class_context):
        cls.step("Create new transfer for each category")
        cls.transfers = []
        for category in DataSet.CATEGORIES:
            cls.transfers.append(Transfer.api_create(class_context, category, is_public=False, org_guid=test_org.guid,
                                                     source=Urls.test_transfer_link))
        cls.step("Ensure that transfers are finished")
        for transfer in cls.transfers:
            transfer.ensure_finished()
        cls.step("Get all data sets in the test org")
        transfer_titles = [t.title for t in cls.transfers]
        cls.datasets = [d for d in DataSet.api_get_list(org_list=[test_org]) if d.title in transfer_titles]

    @pytest.fixture(scope="function")
    def setup_context(self, context):
        # TODO no longer needed when this class removes unittest dependency
        self.context = context

    def _filter_datasets(self, org, filters=(), only_private=False, only_public=False):
        ds_list = DataSet.api_get_list(org_list=[org], filters=filters, only_private=only_private,
                                       only_public=only_public)
        return [d for d in ds_list if d in self.datasets]

    @priority.high
    def test_match_dataset_to_transfer(self):
        self.step("Check if a data set was created for each transfer")
        missing_ds = []
        dataset_titles = [ds.title for ds in self.datasets]
        for tr in self.transfers:
            if tr.title not in dataset_titles:
                missing_ds.append(tr.title)
        self.assertEqual(missing_ds, [], "Missing datasets: {}".format(missing_ds))

    @priority.medium
    def test_get_datasets_by_category(self):
        self.step("Retrieve datasets by categories")
        for category in DataSet.CATEGORIES:
            with self.subTest(category=category):
                filtered_datasets = self._filter_datasets(test_data.TestData.test_org, ({"category": [category]},))
                expected_datasets = [d for d in self.datasets if d.category == category]
                self.assertListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_get_datasets_by_creation_date(self):
        self.step("Sort datasets by creation time and retrieve first two")
        time_range = sorted([dataset.creation_time for dataset in self.datasets][:2])
        self.step("Retrieve datasets for specified time range")
        filtered_datasets = self._filter_datasets(test_data.TestData.test_org, ({"creationTime": time_range},))
        expected_datasets = [d for d in self.datasets if time_range[0] <= d.creation_time <= time_range[1]]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_get_datasets_by_file_format(self):
        # Test should be updated when we will receive answer about supported file formats.
        self.step("Retrieve datasets by file format")
        for file_format in DataSet.FILE_FORMATS:
            with self.subTest(file_format=file_format):
                filtered_datasets = self._filter_datasets(test_data.TestData.test_org, ({"format": [file_format]},))
                expected_datasets = [d for d in self.datasets if d.format == file_format]
                self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    @pytest.mark.public_dataset
    def test_get_public_datasets_from_current_org(self):
        self.step("Retrieve only public datasets")
        filtered_datasets = self._filter_datasets(test_data.TestData.test_org, only_public=True)
        expected_datasets = [d for d in self.datasets if d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_get_private_datasets_from_current_org(self):
        self.step("Retrieve only private datasets")
        filtered_datasets = self._filter_datasets(test_data.TestData.test_org, only_private=True)
        expected_datasets = [d for d in self.datasets if not d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_compare_dataset_details_with_transfer_details(self):
        self.step("Get transfer and matching dataset")
        transfer = self.transfers[0]
        dataset = next(iter([ds for ds in self.datasets if ds.title == transfer.title]), None)
        self.step("Check that dataset exists for chosen transfer")
        self.assertIsNotNone(dataset, "Dataset doesn't exist for transfer {}".format(transfer))
        self.step("Check dataset and transfer category")
        self.assertEqual(dataset.category, transfer.category)
        self.step("Check dataset and transfer org guid")
        self.assertEqual(dataset.org_guid, transfer.organization_guid)
        self.step("Check dataset and transfer file format")
        self.assertEqual(dataset.format, "CSV")
        self.step("Check dataset and transfer public status")
        self.assertEqual(dataset.is_public, transfer.is_public)
        self.step("Check dataset and transfer source uri")
        self.assertEqual(dataset.source_uri, transfer.source)

    @priority.medium
    @pytest.mark.usefixtures("setup_context")
    def test_get_data_sets_from_another_org(self):
        self.step("Create another test organization")
        org = Organization.api_create(self.context)
        self.step("Retrieve datasets from the new org")
        public_datasets = [ds for ds in self.datasets if ds.is_public]
        private_datasets = [ds for ds in self.datasets if not ds.is_public]
        datasets = [ds for ds in DataSet.api_get_list(org_list=[org])]
        self.step("Check that no private data sets are visible in another org")
        self.found_private_ds = [ds for ds in private_datasets if ds in datasets]
        self.assertUnorderedListEqual(self.found_private_ds, [], "Private datasets from another org returned")
        self.step("Check that all public data sets are visible in another org")
        self.missing_public_ds = [ds for ds in public_datasets if ds not in datasets]
        self.assertUnorderedListEqual(self.missing_public_ds, [], "Not all public data sets from another org returned")