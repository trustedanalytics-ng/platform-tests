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
from modules.tap_logger import step
from modules.markers import priority
from modules.tap_object_model.flows import data_catalog


logged_components = (TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)]


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class TestDataSetFromHdfs(object):

    TEST_FILE_URL = Urls.test_transfer_link

    @priority.medium
    def test_create_dataset_from_hdfs_uri(self, context, test_org):
        step("Create source dataset")
        _, source_dataset = data_catalog.create_dataset_from_link(context, test_org.guid, self.TEST_FILE_URL)
        step("Create dataset from hdfs uri")
        _, dataset = data_catalog.create_dataset_from_link(context, test_org.guid, source_dataset.target_uri)
        assert dataset.source_uri == source_dataset.target_uri
