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
import unittest

from modules.constants import TapComponent as TAP, Urls
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import cleanup_after_failed_setup, TapTestCase
from modules.runner.decorators import components, priority
from modules.service_tools.atk import ATKtools
from modules.tap_object_model import Application, DataSet, Organization, Space, Transfer, User


@log_components()
@components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class DataSetFromHdfs(TapTestCase):
    atk_virtualenv = None
    atk_url = None

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and space")
        cls.org = Organization.api_create()
        cls.space = Space.api_create(cls.org)
        cls.step("Get reference space")
        _, cls.ref_space = Organization.get_ref_org_and_space()
        cls.step("Add admin to the test space")
        admin_user = User.get_admin()
        admin_user.api_add_to_space(space_guid=cls.space.guid, org_guid=cls.org.guid, roles=("managers", "developers"))
        cls.atk_virtualenv = ATKtools("atk_virtualenv")

    @classmethod
    def tearDownClass(cls):
        cls.atk_virtualenv.teardown(atk_url=cls.atk_url, org=cls.org)
        super().tearDownClass()

    def _create_dataset(self, org, source, is_public=False, category=DataSet.CATEGORIES[0]):
        self.step("Create new transfer")
        transfer = Transfer.api_create(org_guid=org.guid, source=source, category=category, is_public=is_public)
        self.step("Wait for transfer to finish")
        transfer.ensure_finished()
        self.step("Get data set matching to transfer")
        return DataSet.api_get_matching_to_transfer([org], transfer.title)

    @priority.medium
    def test_create_dataset_from_hdfs_uri(self):
        self.step("Create source dataset")
        source_dataset = self._create_dataset(self.org, Urls.test_transfer_link)
        self.step("Create dataset from hdfs uri")
        dataset = self._create_dataset(self.org, source_dataset.target_uri)
        self.assertEqual(dataset.source_uri, source_dataset.target_uri)

    @priority.low
    @unittest.skip("We don't know how this should work")
    def test_create_transfer_from_atk_model_file(self):
        model_path = os.path.join("fixtures", "data_sets", "lda.csv")
        test_data_directory = os.path.join("fixtures", "atk_test_scripts")
        self.step("Create transfer")
        initial_transfer = Transfer.api_create_by_file_upload(org_guid=self.org.guid, file_path=model_path)
        initial_transfer.ensure_finished()
        initial_dataset = DataSet.api_get_matching_to_transfer([self.org], initial_transfer.title)
        self.step("Get atk app from seedspace")
        atk_app = next((app for app in Application.cf_api_get_list_by_space(self.ref_space.guid) if app.name == "atk"), None)
        if atk_app is None:
            raise AssertionError("Atk app not found in seedspace")
        self.step("Create virtualenv")
        self.atk_virtualenv.create()
        self.step("Install the atk client package")
        self.atk_virtualenv.pip_install(ATKtools.get_atk_client_url(atk_app.urls[0]))
        self.step("Run atk create model script")
        ATKtools.check_uaac_token()
        atk_test_script_path = os.path.join(test_data_directory, "atk_create_model.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, atk_app.urls[0],
                                                      arguments={"--target_uri": initial_dataset.target_uri})
        self.step("Retrieve path to model file created by atk")
        hdfs_model_path = response.split("hdfs_model_path: ", 1)[1]
        self.step("Create dataset by providing retrieved model file path")
        ds = self._create_dataset(self.org, source=hdfs_model_path)
        self.assertEqual(ds.source_uri, hdfs_model_path)