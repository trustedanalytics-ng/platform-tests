#
# Copyright (c) 2017 Intel Corporation
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

from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Transfer

logged_components = (TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)]


class TestGetDataSets(object):

    data_sample = ["COL_0", "COL_1", "COL_2", "COL_3", "COL_4", "COL_5", "COL_6", "COL_7"]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_test_data_sets(cls, request, test_org, class_context, test_data_urls):
        step("Create new transfer for each category")
        cls.transfers = []
        for category in DataSet.CATEGORIES:
            cls.transfers.append(Transfer.api_create(class_context, category, is_public=False, org_guid=test_org.guid,
                                                     source=test_data_urls.test_transfer.url))
        for category in DataSet.CATEGORIES:
            cls.transfers.append(Transfer.api_create(class_context, category, is_public=True, org_guid=test_org.guid,
                                                     source=test_data_urls.test_transfer.url))
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

    @priority.medium
    def test_get_datasets_by_keyword_title(self, test_org):
        """
        <b>Description:</b>
        Check that dataset can be retrieved by title.

        <b>Input data:</b>
        1. transfer title
        2. dataset list

        <b>Expected results:</b>
        Test passes when dataset can be retrieved by title.

        <b>Steps:</b>
        1. Retrieve dataset by title.
        2. Check that retrieved dataset is correct.
        """
        title = self.transfer_titles[0]
        step("Retrieve datasets by title keyword")
        filtered_datasets = self._filter_datasets(test_org, query=title)
        expected_datasets = [d for d in self.datasets if d.title == title]
        assert sorted(filtered_datasets) == sorted(expected_datasets)