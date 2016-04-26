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

import time

from modules.constants import DataCatalogHttpStatus as HttpStatus, TapComponent as TAP, Urls
from modules.file_utils import generate_csv_file, tear_down_test_files
from modules.http_calls import platform as api
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from modules.runner.decorators import components, priority
from modules.tap_object_model import DataSet, Organization, Transfer, User
from modules.test_names import get_test_name


class SubmitTransferBase(TapTestCase):
    DEFAULT_CATEGORY = "other"

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)


@log_components()
@components(TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class SubmitTransfer(SubmitTransferBase):
    MSG_ON_INVALID_ORG_GUID = HttpStatus.MSG_NOT_VALID_UUID

    def _create_transfer(self, org_guid, category):
        self.step("Create new transfers and wait until they finish")
        transfer = Transfer.api_create(category=category, source=Urls.test_transfer_link, org_guid=org_guid)
        transfer.ensure_finished()
        return transfer

    @priority.high
    def test_submit_transfer(self):
        transfer = self._create_transfer(category=self.DEFAULT_CATEGORY, org_guid=self.org.guid)
        self.step("Get transfers and check if they are the same as the uploaded ones")
        retrieved_transfer = Transfer.api_get(transfer.id)
        self.assertEqual(transfer, retrieved_transfer, "The transfer is not the same")

    @priority.low
    def test_create_transfer_with_new_category(self):
        new_category = "user_category"
        transfer = self._create_transfer(category=new_category, org_guid=self.org.guid)
        self.step("Get transfer and check it's category")
        retrieved_transfer = Transfer.api_get(transfer.id)
        self.assertEqual(retrieved_transfer.category, new_category, "Created transfer has different category")

    @priority.low
    def test_cannot_create_transfer_when_providing_invalid_org_guid(self):
        org_guid = "invalid_guid"
        self.step("Try create a transfer by providing invalid org guid")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, self.MSG_ON_INVALID_ORG_GUID,
                                            self._create_transfer, org_guid=org_guid, category=self.DEFAULT_CATEGORY)

    @priority.low
    def test_create_transfer_without_category(self):
        """DPNG-6074 Transfer (from link) without category timeouts"""        
        transfer = self._create_transfer(category=None, org_guid=self.org.guid)
        self.step("Get transfer and check it's category")
        transfer_list = Transfer.api_get_list(org_guid_list=[self.org.guid])
        transfer.category = "other"
        self.assertIn(transfer, transfer_list, "Transfer was not found")

    @priority.medium
    def test_no_token_in_create_transfer_response(self):
        self.step("Create new transfer and check that 'token' field was not returned in response")
        response = api.api_create_transfer(
            source=Urls.test_transfer_link,
            title=get_test_name(),
            is_public=False,
            org_guid=self.org.guid,
            category=self.DEFAULT_CATEGORY
        )
        self.assertTrue("token" not in response, "token field was returned in response")


@log_components()
@components(TAP.das, TAP.hdfs_uploader, TAP.metadata_parser)
class SubmitTransferFromLocalFile(SubmitTransfer):
    MSG_ON_INVALID_ORG_GUID = HttpStatus.MSG_BAD_REQUEST

    def _create_transfer(self, org_guid, column_count=10, row_count=10, category=SubmitTransfer.DEFAULT_CATEGORY, size=None, file_name=None):
        self.step("Generate sample csv file")
        file_path = generate_csv_file(column_count=column_count, row_count=row_count, size=size, file_name=file_name)
        self.step("Create a transfer with new category")
        transfer = Transfer.api_create_by_file_upload(category=category, org_guid=org_guid, file_path=file_path)
        transfer.ensure_finished()
        return transfer

    def tearDown(self):
        tear_down_test_files()

    @priority.medium
    def test_submit_transfer_from_large_file(self):
        transfer = self._create_transfer(org_guid=self.org.guid, size=20 * 1024 * 1024)
        self.step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], transfer.title)

    @priority.low
    def test_create_transfer_without_category(self):
        """DPNG-3678 Create transfer by file upload without category - http 500"""
        return super().test_create_transfer_without_category()

    @priority.medium
    def test_no_token_in_create_transfer_response(self):
        self.step("Generate sample csv file")
        file_path = generate_csv_file(column_count=10, row_count=10)
        self.step("Create new transfer and check that 'token' field was not returned in response")
        response = api.api_create_transfer_by_file_upload(
            source=file_path,
            title="test-transfer-{}".format(time.time()),
            is_public=False,
            org_guid=self.org.guid,
            category=self.DEFAULT_CATEGORY
        )
        self.assertTrue("token" not in response, "token field was returned in response")

    @priority.low
    def test_submit_transfer_from_file_with_space_in_name(self):
        transfer = self._create_transfer(org_guid=self.org.guid, file_name="test file with space in name {}.csv")
        self.step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], transfer.title)

    @priority.low
    def test_submit_transfer_from_empty_file(self):
        transfer = self._create_transfer(org_guid=self.org.guid, category=self.DEFAULT_CATEGORY, size=0)
        self.step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], transfer.title)


@log_components()
@components(TAP.das)
class GetTransfers(TapTestCase):
    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    @priority.high
    def test_admin_can_get_transfer_list(self):
        self.step("Check if the list of transfers can be retrieved")
        Transfer.api_get_list(org_guid_list=[self.org.guid])
