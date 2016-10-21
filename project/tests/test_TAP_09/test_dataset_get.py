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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Organization

logged_components = (TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)]


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class TestGetDataSets(object):

    @priority.medium
    @pytest.mark.skip("Skipped until there is possibility to have more than one organization")
    def test_get_data_sets_from_another_org(self, context):
        step("Create another test organization")
        org = Organization.create(context)
        step("Retrieve datasets from the new org")
        public_datasets = [ds for ds in self.datasets if ds.is_public]
        private_datasets = [ds for ds in self.datasets if not ds.is_public]
        datasets = [ds for ds in DataSet.api_get_list(org_guid_list=[org.guid])]
        step("Check that no private data sets are visible in another org")
        found_private_ds = [ds for ds in private_datasets if ds in datasets]
        assert found_private_ds == [], "Private datasets from another org returned"
        step("Check that all public data sets are visible in another org")
        missing_public_ds = [ds for ds in public_datasets if ds not in datasets]
        assert missing_public_ds == [], "Not all public data sets from another org returned"
