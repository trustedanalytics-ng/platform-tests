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

import os
from datetime import datetime

import pytest

from modules.constants import TapComponent as TAP
from modules.file_utils import get_csv_data, get_csv_record_count, get_csv_first_row
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Application, DataSet, DatasetAccess as Access, Transfer

logged_components = (TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)]


class TestCreateDataSets(object):

    DETAILS_TO_COMPARE = {
        "accessibility",
        "title",
        "category",
        "sourceUri",
        "size",
        "orgUUID",
        "format",
        "dataSample",
        "isPublic",
        "creationTime",
    }

    @classmethod
    @pytest.fixture(scope="class", autouse=False)
    def target_uri(cls, test_org):
        step("Get target uri from hdfs instance")
        hdfs = next(app for app in Application.get_list() if "hdfs-downloader" in app.name)
        cls.target_uri = hdfs.cf_api_env()['VCAP_SERVICES']['hdfs'][0]['credentials']['uri']
        cls.target_uri = cls.target_uri.replace("%{organization}", test_org.guid)

    @classmethod
    @pytest.fixture(scope="class")
    def transfer(cls, class_context, test_org, test_data_urls):
        step("Create transfer by providing a csv from url")
        transfer = Transfer.api_create(class_context, org_guid=test_org.guid, source=test_data_urls.test_transfer.url)
        transfer.ensure_finished()
        return transfer

    @pytest.fixture(scope="class")
    def dataset(self, transfer, test_org):
        step("Get data set matching to transfer {}".format(transfer.title))
        return DataSet.api_get_matching_to_transfer(org_guid=test_org.guid, transfer_title=transfer.title)

    @pytest.fixture(scope="class")
    def expected_dataset_details(self, test_org, test_data_urls, transfer):
        return {
            'accessibility': Access.PRIVATE.name,
            'title': transfer.title,
            'category': transfer.category,
            'recordCount': get_csv_record_count(test_data_urls.test_transfer.filepath),
            'sourceUri': test_data_urls.test_transfer.url,
            'size': os.path.getsize(test_data_urls.test_transfer.filepath),
            'orgUUID': test_org.guid,
            'format': "CSV",
            'dataSample': ",".join(get_csv_first_row(test_data_urls.test_transfer.filepath)),
            'isPublic': Access.PRIVATE.value,
            'creationTime': datetime.utcfromtimestamp(transfer.timestamps["FINISHED"]).strftime("%Y-%m-%dT%H:%M")
        }

    @priority.medium
    @pytest.mark.parametrize("key", DETAILS_TO_COMPARE)
    def test_create_dataset(self, key, dataset, expected_dataset_details):
        """
        <b>Description:</b>
        Check that dataset can be created.

        <b>Input data:</b>
        1. organization id
        2. source file
        3. list of metadata types to compare
        4. transfer category
        5. transfer title

        <b>Expected results:</b>
        Test passes when dataset is successfully created and has expected details.

        <b>Steps:</b>
        1. Create private transfer from file/url.
        2. Get dataset that matches the created transfer.
        3. Compare dataset details with expected details.
        """
        step("Compare dataset details with expected values")
        assert expected_dataset_details[key] == dataset.get_details()[key]

    @priority.medium
    def test_create_dataset_recordcount(self, dataset, test_data_urls):
        """
        <b>Description:</b>
        Check that dataset record count is the same as in the source file.

        <b>Input data:</b>
        1. Created dataset
        2. Source file

        <b>Expected results:</b>
        Dataset record count is the same as in the source file.

        <b>Steps:</b>
        1. Get created dataset.
        2. Compare dataset record count with source file record count.
        """
        step("Check that record count is valid")
        assert dataset.record_count == get_csv_record_count(test_data_urls.test_transfer.filepath)


class TestCreateDataSetsFromFile(TestCreateDataSets):

    @pytest.fixture(scope="class")
    def expected_dataset_details(self, test_org, test_data_urls, transfer):
        return {
            'accessibility': Access.PRIVATE.name,
            'title': transfer.title,
            'category': transfer.category,
            'recordCount': get_csv_record_count(test_data_urls.test_transfer.filepath),
            'sourceUri': os.path.split(test_data_urls.test_transfer.filepath)[1],
            'size': os.path.getsize(test_data_urls.test_transfer.filepath),
            'orgUUID': test_org.guid,
            'format': "CSV",
            'dataSample': ",".join(get_csv_first_row(test_data_urls.test_transfer.filepath)),
            'isPublic': Access.PRIVATE.value,
            'creationTime': datetime.utcfromtimestamp(transfer.timestamps["FINISHED"]).strftime("%Y-%m-%dT%H:%M")
        }

    @pytest.fixture(scope="class")
    def transfer(self, class_context, test_org, test_data_urls):
        step("Create transfer by uploading csv file")
        transfer = Transfer.api_create_by_file_upload(class_context, test_org.guid,
                                                      file_path=test_data_urls.test_transfer.filepath)
        transfer.ensure_finished()
        return transfer
