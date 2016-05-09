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

import os
import datetime

import pytest

from modules.constants import TapComponent as TAP, Urls
from modules.file_utils import download_file, get_csv_data, get_csv_record_count
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.tap_object_model import Application, DataSet, Transfer
from tests.fixtures.test_data import TestData


logged_components = (TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [components.data_catalog, components.das, components.hdfs_downloader, components.metadata_parser]


@pytest.mark.usefixtures("test_org", "add_admin_to_test_org")
class CreateDatasets(TapTestCase):
    DETAILS_TO_COMPARE = {"accessibility", "title", "category", "sourceUri", "size", "orgUUID", "targetUri", "format",
                          "dataSample", "isPublic", "creationTime"}
    ACCESSIBILITIES = {True: "PUBLIC", False: "PRIVATE"}
    FROM_FILE = False

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def target_uri(cls, test_org, core_space):
        cls.step("Get target uri from hdfs instance")
        hdfs = next(app for app in Application.cf_api_get_list_by_space(core_space.guid) if "hdfs-downloader" in app.name)
        cls.target_uri = hdfs.cf_api_env()['VCAP_SERVICES']['hdfs'][0]['credentials']['uri'].replace("%{organization}",
                                                                                                     TestData.test_org.guid)

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def data_set_file_path(cls):
        source = Urls.test_transfer_link
        cls.file_path = download_file(source)

    def _get_expected_dataset_details(self, org_uuid, format, is_public, file_path, transfer, from_file=False):
        return {'accessibility': self.ACCESSIBILITIES[is_public], 'title': transfer.title,
                'category': transfer.category, 'recordCount': get_csv_record_count(file_path),
                'sourceUri': os.path.split(file_path)[1] if from_file else Urls.test_transfer_link,
                'size': os.path.getsize(file_path), 'orgUUID': org_uuid,
                'targetUri': self.target_uri + "{}".format(transfer.id_in_object_store), 'format': format,
                'dataSample': ",".join(get_csv_data(file_path)), 'isPublic': is_public,
                'creationTime': datetime.datetime.utcfromtimestamp(transfer.timestamps["FINISHED"]).strftime(
                    "%Y-%m-%dT%H:%M")}

    def _get_transfer_and_dataset(self, file_source, is_public):
        self.step("Create transfer by providing a csv from url")
        transfer = Transfer.api_create(DataSet.CATEGORIES[0], is_public, TestData.test_org.guid, file_source)
        transfer.ensure_finished()
        self.step("Get data set matching to transfer {}".format(transfer.title))
        data_set = DataSet.api_get_matching_to_transfer(org=TestData.test_org, transfer_title=transfer.title)
        return transfer, data_set

    @priority.medium
    def test_create_dataset(self):
        for is_public, access in self.ACCESSIBILITIES.items():
            transfer, dataset = self._get_transfer_and_dataset(Urls.test_transfer_link, is_public)
            self.step("Generate expected dataset summary and get real dataset summary")
            expected_details = self._get_expected_dataset_details(TestData.test_org.guid, "CSV", is_public,
                                                                  self.file_path, transfer, from_file=self.FROM_FILE)
            ds_details = dataset.get_details()
            self.step("Compare dataset details with expected values")
            for key in self.DETAILS_TO_COMPARE:
                with self.subTest(accessibility=access, detail=key):
                    self.assertEqual(expected_details[key], ds_details[key])

    @priority.medium
    @pytest.mark.bugs("DPNG-3656 Wrong record count for csv file in dataset details")
    def test_create_dataset_recordcount(self):
        label = "recordCount"
        for is_public, access in self.ACCESSIBILITIES.items():
            transfer, dataset = self._get_transfer_and_dataset(Urls.test_transfer_link, is_public)
            with self.subTest(accessibility=access, detail=label):
                self.assertEqual(dataset.record_count, get_csv_record_count(self.file_path))