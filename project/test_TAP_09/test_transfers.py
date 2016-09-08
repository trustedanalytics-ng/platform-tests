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

from modules.constants import DataCatalogHttpStatus as HttpStatus, TapComponent as TAP
from modules.file_utils import generate_csv_file
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Transfer, Organization
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.das, TAP.downloader, TAP.uploader, TAP.metadata_parser)


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class TestSubmitTransfer:
    pytestmark = [pytest.mark.components(TAP.das, TAP.downloader, TAP.metadata_parser)]

    DEFAULT_CATEGORY = "other"

    def _create_transfer(self, context, org_guid, category, test_data_urls):
        step("Create new transfer and wait until it's finished")
        transfer = Transfer.api_create(context, category=category, source=test_data_urls.test_transfer.url,
                                       org_guid=org_guid)
        transfer.ensure_finished()
        return transfer

    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    def test_transfer_and_dataset_are_not_visible_in_other_org(self, context, core_org, test_org, test_data_urls):
        step("Create transfer and get dataset")
        transfer = self._create_transfer(context, category=self.DEFAULT_CATEGORY, org_guid=test_org.guid,
                                         test_data_urls=test_data_urls)
        dataset = DataSet.api_get_matching_to_transfer(org_guid=test_org.guid, transfer_title=transfer.title)
        step("Check transfer is not visible on other organization")
        transfers = Transfer.api_get_list(org_guid_list=[core_org.guid])
        assert transfer not in transfers
        step("Check dataset is not visible on other organization")
        datasets = DataSet.api_get_list(org_guid_list=[core_org.guid])
        assert dataset not in datasets


class TestSubmitTransferFromLocalFile(TestSubmitTransfer):
    pytestmark = [pytest.mark.components(TAP.das, TAP.downloader, TAP.uploader, TAP.metadata_parser)]

    def _create_transfer(self, context, org_guid, column_count=10, row_count=10,
                         category=TestSubmitTransfer.DEFAULT_CATEGORY, size=None, file_name=None):
        step("Generate sample file")
        file_path = generate_csv_file(column_count=column_count, row_count=row_count, size=size, file_name=file_name)
        step("Create a transfer with new category")
        transfer = Transfer.api_create_by_file_upload(context, category=category, org_guid=org_guid,
                                                      file_path=file_path)
        transfer.ensure_finished()
        return transfer

    @priority.high
    @pytest.mark.skip(reason="OUT OF SCOPE FOR 0.8 - multiple orgs")
    def test_cannot_submit_transfer_in_foreign_org(self, context):
        foreign_org = Organization.api_create(context=context)
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN, self._create_transfer,
                                     context, org_guid=foreign_org.guid, category=self.DEFAULT_CATEGORY)
