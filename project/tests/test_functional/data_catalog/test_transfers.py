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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, Transfer, Organization
from modules.tap_object_model.flows.data_catalog import create_dataset_from_file
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.das, TAP.downloader, TAP.uploader, TAP.metadata_parser)


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class TestSubmitTransfer:
    pytestmark = [pytest.mark.components(TAP.das, TAP.downloader, TAP.metadata_parser)]

    DEFAULT_CATEGORY = "other"
    MSG_ON_INVALID_ORG_GUID = HttpStatus.MSG_NOT_VALID_UUID
    TEST_FILE_URL = Urls.test_transfer_link

    def _create_transfer(self, context, org_guid, category):
        step("Create new transfer and wait until it's finished")
        transfer = Transfer.api_create(context, category=category, source=self.TEST_FILE_URL, org_guid=org_guid)
        transfer.ensure_finished()
        return transfer

    @staticmethod
    def check_transfer_and_dataset_are_visible_in_test_org(transfer, dataset, test_org):
        step("Check transfer is visible on list of transfers")
        transfers = Transfer.api_get_list(org_guid_list=[test_org.guid])
        assert transfer in transfers
        step("Check dataset is visible on list of datasets")
        datasets = DataSet.api_get_list(org_guid_list=[test_org.guid])
        assert dataset in datasets

    @priority.high
    def test_submit_and_delete_transfer(self, context, test_org):
        """
        <b>Description:</b>
        Check transfer creation from an url and deletion. Also check dataset deletion.

        <b>Input data:</b>
        1. organization guid
        2. transfer category
        3. url with a source file

        <b>Expected results:</b>
        Transfer is successfully created and deleted. Dataset is successfully deleted.

        <b>Steps:</b>
        1. Create transfer.
        2. Retrieve corresponding dataset,
        3. Delete transfer.
        4. Check that transfer disappeared from the transfer list.
        5. Delete dataset.
        6. Check that dataset disappeared from the dataset list.
        """
        transfer = self._create_transfer(context, category=self.DEFAULT_CATEGORY, org_guid=test_org.guid)
        step("Get transfers and check if they are the same as the uploaded ones")
        retrieved_transfer = Transfer.api_get(transfer.id)
        assert transfer == retrieved_transfer, "The transfer is not the same"
        dataset = DataSet.api_get_matching_to_transfer(org_guid=test_org.guid, transfer_title=transfer.title)
        TestSubmitTransfer.check_transfer_and_dataset_are_visible_in_test_org(transfer=transfer, dataset=dataset,
                                                                              test_org=test_org)
        step("Delete transfer")
        transfer.cleanup()
        step("Check transfer is not visible on list of transfers")
        transfers = Transfer.api_get_list(org_guid_list=[test_org.guid])
        assert transfer not in transfers
        step("Delete dataset")
        dataset.cleanup()
        step("Check dataset is not visible on list of datasets")
        datasets = DataSet.api_get_list(org_guid_list=[test_org.guid])
        assert dataset not in datasets

    @priority.low
    def test_create_transfer_with_new_category(self, context, test_org):
        """
        <b>Description:</b>
        Check that transfer can be created from an url with custom category.

        <b>Input data:</b>
        1. organization id
        2. custom category name
        3. url with a source file

        <b>Expected results:</b>
        Transfer is successfully created with custom category.

        <b>Steps:</b>
        1. Create transfer with custom category.
        2. Retrieve transfer from list.
        3. Check that retrieved transfer has a custom category.
        """
        new_category = "user_category"
        transfer = self._create_transfer(context, category=new_category, org_guid=test_org.guid)
        step("Get transfer and check it's category")
        retrieved_transfer = Transfer.api_get(transfer.id)
        assert retrieved_transfer.category == new_category, "Created transfer has different category"

    @priority.low
    def test_cannot_create_transfer_when_providing_invalid_org_guid(self, context):
        """
        <b>Description:</b>
        Try to create transfer from an url by providing invalid organization id.

        <b>Input data:</b>
        1. invalid organization id
        2. url with a source file

        <b>Expected results:</b>
        Transfer cannot be created. Platform returns a 402 http status
        error and a message that provided organizatio id is invalid.

        <b>Steps:</b>
        1. Send a transfer create request with invalid organization id.
        """
        org_guid = "invalid_guid"
        step("Try create a transfer by providing invalid org guid")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, self.MSG_ON_INVALID_ORG_GUID, self._create_transfer,
                                     context, org_guid=org_guid, category=self.DEFAULT_CATEGORY)

    @priority.low
    def test_create_transfer_without_category(self, context, test_org):
        """
        <b>Description:</b>
        Check that transfer can be created from an url without providing a category.

        <b>Input data:</b>
        1. organization id
        2. url with a source file

        <b>Expected results:</b>
        Transfer is successfully created and belongs to 'other' category.

        <b>Steps:</b>
        1. Create transfer without providing a category.
        2. Check that newly created transfer has a 'other' category.
        """
        transfer = self._create_transfer(context, category=None, org_guid=test_org.guid)
        step("Get transfer and check it's category")
        transfer_list = Transfer.api_get_list(org_guid_list=[test_org.guid])
        transfer.category = "other"
        assert transfer in transfer_list, "Transfer was not found"

    @priority.medium
    def test_no_token_in_create_transfer_response(self, test_org):
        """
        <b>Description:</b>
        Check that create transfer from an url response doesn't contain a 'token' field.

        <b>Input data:</b>
        1. organization id
        2. url with a source file

        <b>Expected results:</b>
        Test passes when create transfer response doesn't contain a 'token' field.

        <b>Steps:</b>
        1. Send valid create transfer request.
        2. Check that in the response there is no 'token' field.
        """
        step("Create new transfer and check that 'token' field was not returned in response")
        response = das.api_create_transfer(
            source=self.TEST_FILE_URL,
            title=generate_test_object_name(),
            is_public=False,
            org_guid=test_org.guid,
            category=self.DEFAULT_CATEGORY
        )
        assert "token" not in response, "token field was returned in response"


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class TestSubmitTransferFromLocalFile(TestSubmitTransfer):
    pytestmark = [pytest.mark.components(TAP.das, TAP.downloader, TAP.uploader, TAP.metadata_parser)]

    MSG_ON_INVALID_ORG_GUID = HttpStatus.MSG_BAD_REQUEST

    def _create_transfer(self, context, org_guid, column_count=10, row_count=10,
                         category=TestSubmitTransfer.DEFAULT_CATEGORY, size=None, file_name=None):
        step("Generate sample file")
        file_path = generate_csv_file(column_count=column_count, row_count=row_count, size=size, file_name=file_name)
        step("Create a transfer with new category")
        transfer = Transfer.api_create_by_file_upload(context, category=category, org_guid=org_guid,
                                                      file_path=file_path)
        transfer.ensure_finished()
        return transfer

    @priority.low
    @pytest.mark.parametrize("category", DataSet.CATEGORIES)
    def test_submit_transfer_from_txt_file(self, category, context, test_org):
        """
        <b>Description:</b>
        Check that transfer can be created from a txt file in any category.

        <b>Input data:</b>
        1. organization id
        2. transfer category
        3. test file

        <b>Expected results:</b>
        Test passes when transfer and dataset are successfully created from a txt file
        and are visible in the test organization.

        <b>Steps:</b>
        1. Create transfer from a txt file.
        2. Retrieve created transfer and dataset.
        3. Check that created transfer and dataset are visible in the test organization.
        """
        step("Create txt file name")
        txt_file_name = "{}.txt".format(generate_test_object_name())
        step("Create transfer from file")
        transfer, dataset = create_dataset_from_file(context=context, org_guid=test_org.guid,
                                                     file_path=generate_csv_file(file_name=txt_file_name),
                                                     category=category)
        TestSubmitTransfer.check_transfer_and_dataset_are_visible_in_test_org(transfer=transfer, dataset=dataset,
                                                                              test_org=test_org)

    @priority.low
    @pytest.mark.parametrize("category", DataSet.CATEGORIES)
    def test_submit_transfer_from_csv_file_all_categories(self, context, category, test_org):
        """
        <b>Description:</b>
        Check that transfer can be created from a csv file in any category.

        <b>Input data:</b>
        1. organization id
        2. transfer category
        3. test file

        <b>Expected results:</b>
        Test passes when transfer and dataset are successfully created from a csv file
        and are visible in the test organization.

        <b>Steps:</b>
        1. Create transfer from a csv file.
        2. Retrieve created transfer and dataset.
        3. Check that created transfer and dataset are visible in the test organization.
        """
        step("Create a transfer with chosen category")
        transfer, dataset = create_dataset_from_file(context=context, org_guid=test_org.guid,
                                                     file_path=generate_csv_file(), category=category)
        TestSubmitTransfer.check_transfer_and_dataset_are_visible_in_test_org(transfer=transfer, dataset=dataset,
                                                                              test_org=test_org)

    @priority.medium
    def test_submit_transfer_from_large_file(self, context, test_org):
        """
        <b>Description:</b>
        Check that transfer can be created from a csv file in any category.

        <b>Input data:</b>
        1. organization id
        2. transfer category
        3. test file

        <b>Expected results:</b>
        Test passes when transfer and dataset are successfully created from a csv file
        and are visible in the test organization.

        <b>Steps:</b>
        1. Create transfer from a csv file.
        2. Retrieve created transfer and dataset.
        3. Check that created transfer and dataset are visible in the test organization.
        """
        transfer = self._create_transfer(context, org_guid=test_org.guid, size=20 * 1024 * 1024)
        step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer(org_guid=test_org.guid, transfer_title=transfer.title)

    @priority.low
    def test_create_transfer_without_category(self, context, test_org):
        """
        <b>Description:</b>
        Check that transfer can be created from a file without providing a category.

        <b>Input data:</b>
        1. organization id
        2. test file

        <b>Expected results:</b>
        Transfer is successfully created and belongs to 'other' category.

        <b>Steps:</b>
        1. Create transfer without providing a category.
        2. Check that newly created transfer has a 'other' category.
        """
        return super().test_create_transfer_without_category(context, test_org)

    @priority.medium
    def test_no_token_in_create_transfer_response(self, test_org):
        """
        <b>Description:</b>
        Check that create transfer from a file response doesn't contain a 'token' field.

        <b>Input data:</b>
        1. organization id
        2. test file

        <b>Expected results:</b>
        Test passes when create transfer response doesn't contain a 'token' field.

        <b>Steps:</b>
        1. Send valid create transfer request.
        2. Check that in the response there is no 'token' field.
        """
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
        """
        <b>Description:</b>
        Check that it's possible to create transfer from a file that contains spaces in name.

        <b>Input data:</b>
        1. organization id
        2. file name with spaces

        <b>Expected results:</b>
        Test passes when transfer is created.

        <b>Steps:</b>
        1. Create transfer.
        2. Get matching dataset of created transfer
        """
        transfer = self._create_transfer(context, org_guid=test_org.guid, file_name="file with space in name {}.csv")
        step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer(org_guid=test_org.guid, transfer_title=transfer.title)

    @priority.low
    def test_submit_transfer_from_empty_file(self, context, test_org):
        """
        <b>Description:</b>
        Check that it's possible to create transfer from an empty file.

        <b>Input data:</b>
        1. organization id
        2. empty file

        <b>Expected results:</b>
        Test passes when transfer is created.

        <b>Steps:</b>
        1. Create transfer.
        2. Get matching dataset of created transfer.
        """
        transfer = self._create_transfer(context, org_guid=test_org.guid, category=self.DEFAULT_CATEGORY, size=0)
        step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer(org_guid=test_org.guid, transfer_title=transfer.title)


@pytest.mark.bugs("DPNG-10412 [TAP-NG] Integration of Data Catalog components into NG")
class GetTransfers:
    pytestmark = [pytest.mark.components(TAP.das)]

    @priority.high
    def test_admin_can_get_transfer_list(self, test_org):
        """
        <b>Description:</b>
        Check that admin can get a transfers list.

        <b>Input data:</b>
        1. organization id

        <b>Expected results:</b>
        Test passes when transfer list is retrieved.

        <b>Steps:</b>
        1. Retrieve transfer list from organization as admin.
        """
        step("Check if the list of transfers can be retrieved")
        Transfer.api_get_list(org_guid_list=[test_org.guid])
