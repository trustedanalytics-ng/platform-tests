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

from modules.constants import TapComponent as TAP, Urls
from modules.file_utils import download_file, get_csv_data, get_csv_record_count
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import Application, DataSet, DatasetAccess as Access, Transfer

logged_components = (TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [components.data_catalog, components.das, components.hdfs_downloader, components.metadata_parser]


class TestCreateDataSets(object):

    DETAILS_TO_COMPARE = {
        "accessibility",
        "title",
        "category",
        "sourceUri",
        "size",
        "orgUUID",
        "targetUri",
        "format",
        "dataSample",
        "isPublic",
        "creationTime",
    }
    FROM_FILE = False

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def target_uri(cls, test_org, add_admin_to_test_org, core_space):
        step("Get target uri from hdfs instance")
        hdfs = next(app for app in Application.cf_api_get_list_by_space(core_space.guid)
                    if "hdfs-downloader" in app.name)
        cls.target_uri = hdfs.cf_api_env()['VCAP_SERVICES']['hdfs'][0]['credentials']['uri']
        cls.target_uri = cls.target_uri.replace("%{organization}", test_org.guid)

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def data_set_file_path(cls):
        source = Urls.test_transfer_link
        cls.file_path = download_file(source)

    def _get_expected_dataset_details(self, org_uuid, format, access, file_path, transfer, from_file=False):
        return {
            'accessibility': access.name,
            'title': transfer.title,
            'category': transfer.category,
            'recordCount': get_csv_record_count(file_path),
            'sourceUri': os.path.split(file_path)[1] if from_file else Urls.test_transfer_link,
            'size': os.path.getsize(file_path),
            'orgUUID': org_uuid,
            'targetUri': self.target_uri + "{}".format(transfer.id_in_object_store),
            'format': format,
            'dataSample': ",".join(get_csv_data(file_path)),
            'isPublic': access.value,
            'creationTime': datetime.utcfromtimestamp(transfer.timestamps["FINISHED"]).strftime("%Y-%m-%dT%H:%M")
        }

    def _get_transfer_and_dataset(self, test_org, file_source, access, context):
        step("Create transfer by providing a csv from url")
        transfer = Transfer.api_create(context, DataSet.CATEGORIES[0], access.value, test_org.guid, file_source)
        transfer.ensure_finished()
        step("Get data set matching to transfer {}".format(transfer.title))
        data_set = DataSet.api_get_matching_to_transfer(org=test_org, transfer_title=transfer.title)
        return transfer, data_set

    def _get_dataset_current_and_expected_details(self, test_org, access, context):
        transfer, dataset = self._get_transfer_and_dataset(test_org, Urls.test_transfer_link, access, context)
        step("Generate expected dataset summary and get real dataset summary")
        expected_details = self._get_expected_dataset_details(test_org.guid, "CSV", access, self.file_path, transfer,
                                                              from_file=self.FROM_FILE)
        ds_details = dataset.get_details()
        return ds_details, expected_details

    @priority.medium
    @pytest.mark.parametrize("key", DETAILS_TO_COMPARE)
    def test_create_private_dataset(self, key, context, test_org):
        ds_details, expected_details = self._get_dataset_current_and_expected_details(test_org, Access.PRIVATE, context)
        step("Compare private dataset details with expected values")
        assert expected_details[key] == ds_details[key]

    @priority.medium
    @pytest.mark.public_dataset
    @pytest.mark.parametrize("key", DETAILS_TO_COMPARE)
    def test_create_public_dataset(self, key, context, test_org):
        ds_details, expected_details = self._get_dataset_current_and_expected_details(test_org, Access.PUBLIC, context)
        step("Compare public dataset details with expected values")
        assert expected_details[key] == ds_details[key]

    @priority.medium
    @pytest.mark.bugs("DPNG-3656 Wrong record count for csv file in dataset details")
    def test_create_private_dataset_recordcount(self, context, test_org):
        transfer, dataset = self._get_transfer_and_dataset(test_org, Urls.test_transfer_link, Access.PRIVATE, context)
        step("Check that record count is valid")
        assert dataset.record_count == get_csv_record_count(self.file_path)

    @priority.medium
    @pytest.mark.public_dataset
    @pytest.mark.bugs("DPNG-3656 Wrong record count for csv file in dataset details")
    def test_create_public_dataset_recordcount(self, context, test_org):
        transfer, dataset = self._get_transfer_and_dataset(test_org, Urls.test_transfer_link, Access.PUBLIC, context)
        step("Check that record count is valid")
        assert dataset.record_count == get_csv_record_count(self.file_path)
