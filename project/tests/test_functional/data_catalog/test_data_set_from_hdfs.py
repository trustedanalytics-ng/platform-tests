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

from modules.constants import TapComponent as TAP
from modules.tap_logger import step
from modules.markers import priority
from modules.tap_object_model.flows import data_catalog


logged_components = (TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)]


class TestDataSetFromHdfs(object):

    @priority.medium
    def test_create_dataset_from_hdfs_uri(self, context, test_org, test_data_urls):
        """
        <b>Description:</b>
        Check that dataset can be created by passing hdfs uri as source.

        <b>Input data:</b>
        1. organization id
        2. hdfs URI

        <b>Expected results:</b>
        Test passes when dataset is successfully created and it has a hdfs uri in source_uri property.

        <b>Steps:</b>
        1. Create dataset from an url.
        3. Get dataset target_uri (hdfs path) and create new dataset with it.
        4. Compare second dataset source_uri is the same as first dataset target_uri.
        """
        step("Create source dataset")
        _, source_dataset = data_catalog.create_dataset_from_link(context, test_org.guid, test_data_urls.test_transfer.url)
        step("Create dataset from hdfs uri")
        _, dataset = data_catalog.create_dataset_from_link(context, test_org.guid, source_dataset.target_uri)
        assert dataset.source_uri == source_dataset.target_uri
