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

import time

import pytest

from modules.constants import DataCatalogHttpStatus as HttpStatus, TapComponent as TAP, Urls
from modules.file_utils import generate_csv_file
from modules.http_calls.platform import das, hdfs_uploader
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Transfer
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.das, TAP.hdfs_downloader, TAP.hdfs_uploader, TAP.metadata_parser)


@pytest.mark.usefixtures("add_admin_to_test_org")
class TestSubmitTransfer:
    pytestmark = [components.das, components.hdfs_downloader, components.metadata_parser]

    DEFAULT_CATEGORY = "other"
    MSG_ON_INVALID_ORG_GUID = HttpStatus.MSG_NOT_VALID_UUID

    def _create_transfer(self, context, org_guid, category):
        step("Create new transfer and wait until it's finished")
        transfer = Transfer.api_create(context, category=category, source=Urls.test_transfer_link, org_guid=org_guid)
        transfer.ensure_finished()
        return transfer

    @priority.high
    def test_submit_transfer(self, context, test_org):
        transfer = self._create_transfer(context, category=self.DEFAULT_CATEGORY, org_guid=test_org.guid)
        step("Get transfers and check if they are the same as the uploaded ones")
        retrieved_transfer = Transfer.api_get(transfer.id)
        assert transfer == retrieved_transfer, "The transfer is not the same"

    @priority.low
    def test_create_transfer_with_new_category(self, context, test_org):
        new_category = "user_category"
        transfer = self._create_transfer(context, category=new_category, org_guid=test_org.guid)
        step("Get transfer and check it's category")
        retrieved_transfer = Transfer.api_get(transfer.id)
        assert retrieved_transfer.category == new_category, "Created transfer has different category"

    @priority.low
    def test_cannot_create_transfer_when_providing_invalid_org_guid(self, context):
        org_guid = "invalid_guid"
        step("Try create a transfer by providing invalid org guid")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, self.MSG_ON_INVALID_ORG_GUID,
                                     self._create_transfer, context, org_guid=org_guid, category=self.DEFAULT_CATEGORY)

    @priority.low
    @pytest.mark.bugs("DPNG-6074 Transfer (from link) without category timeouts")
    def test_create_transfer_without_category(self, context, test_org):
        transfer = self._create_transfer(context, category=None, org_guid=test_org.guid)
        step("Get transfer and check it's category")
        transfer_list = Transfer.api_get_list(org_guid_list=[test_org.guid])
        transfer.category = "other"
        assert transfer in transfer_list, "Transfer was not found"

    @priority.medium
    def test_no_token_in_create_transfer_response(self, test_org):
        step("Create new transfer and check that 'token' field was not returned in response")
        response = das.api_create_transfer(
            source=Urls.test_transfer_link,
            title=generate_test_object_name(),
            is_public=False,
            org_guid=test_org.guid,
            category=self.DEFAULT_CATEGORY
        )
        assert "token" not in response, "token field was returned in response"


class TestSubmitTransferFromLocalFile(TestSubmitTransfer):
    pytestmark = [components.das, components.hdfs_downloader, components.metadata_parser]

    MSG_ON_INVALID_ORG_GUID = HttpStatus.MSG_BAD_REQUEST

    def _create_transfer(self, context, org_guid, column_count=10, row_count=10, category=TestSubmitTransfer.DEFAULT_CATEGORY,
                         size=None, file_name=None):
        step("Generate sample csv file")
        file_path = generate_csv_file(column_count=column_count, row_count=row_count, size=size, file_name=file_name)
        step("Create a transfer with new category")
        transfer = Transfer.api_create_by_file_upload(context, category=category, org_guid=org_guid,
                                                      file_path=file_path)
        transfer.ensure_finished()
        return transfer

    @priority.medium
    def test_submit_transfer_from_large_file(self, context, test_org):
        transfer = self._create_transfer(context, org_guid=test_org.guid, size=20 * 1024 * 1024)
        step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer(org=test_org, transfer_title=transfer.title)

    @priority.low
    @pytest.mark.bugs("DPNG-3678 Create transfer by file upload without category - http 500")
    def test_create_transfer_without_category(self, context, test_org):
        return super().test_create_transfer_without_category(context, test_org)

    @priority.medium
    def test_no_token_in_create_transfer_response(self, test_org):
        step("Generate sample csv file")
        file_path = generate_csv_file(column_count=10, row_count=10)
        step("Create new transfer and check that 'token' field was not returned in response")
        response = hdfs_uploader.api_create_transfer_by_file_upload(
            source=file_path,
            title="test-transfer-{}".format(time.time()),
            is_public=False,
            org_guid=test_org.guid,
            category=self.DEFAULT_CATEGORY
        )
        assert "token" not in response, "token field was returned in response"

    @priority.low
    def test_submit_transfer_from_file_with_space_in_name(self, context, test_org):
        transfer = self._create_transfer(context, org_guid=test_org.guid, file_name="file with space in name {}.csv")
        step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer(org=test_org, transfer_title=transfer.title)

    @priority.low
    def test_submit_transfer_from_empty_file(self, context, test_org):
        transfer = self._create_transfer(context, org_guid=test_org.guid, category=self.DEFAULT_CATEGORY, size=0)
        step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer(org=test_org, transfer_title=transfer.title)


class GetTransfers:
    pytestmark = [components.das]

    @priority.high
    def test_admin_can_get_transfer_list(self, test_org):
        step("Check if the list of transfers can be retrieved")
        Transfer.api_get_list(org_guid_list=[test_org.guid])
