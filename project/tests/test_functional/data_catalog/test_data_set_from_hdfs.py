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

import pytest

from modules.constants import TapComponent as TAP, Urls
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.service_tools.atk import ATKtools
from modules.tap_object_model import Application
from modules.tap_object_model.flows import data_catalog
from tests.fixtures.test_data import TestData


logged_components = (TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
pytestmark = [components.data_catalog, components.das, components.hdfs_downloader, components.metadata_parser]


@pytest.mark.usefixtures("test_org", "add_admin_to_test_org")
class DataSetFromHdfs(TapTestCase):

    @pytest.fixture(scope="function", autouse=True)
    def cleanup(self, context):
        # TODO move to methods when dependency on unittest is removed
        self.context = context

    @priority.medium
    def test_create_dataset_from_hdfs_uri(self):
        self.step("Create source dataset")
        _, source_dataset = data_catalog.create_dataset_from_link(self.context, TestData.test_org,
                                                                  Urls.test_transfer_link)
        self.step("Create dataset from hdfs uri")
        _, dataset = data_catalog.create_dataset_from_link(self.context, TestData.test_org, source_dataset.target_uri)
        self.assertEqual(dataset.source_uri, source_dataset.target_uri)

    @classmethod
    @pytest.fixture(scope="function")
    def atk_virtualenv(cls, request):
        cls.atk_virtualenv = ATKtools("atk_virtualenv")

        def fin():
            cls.atk_virtualenv.teardown(atk_url=cls.atk_url, org=TestData.test_org)
        request.addfinalizer(fin)

    @pytest.fixture(scope="function")
    def create_data_set(self, request, context):
        self.step("Create data set from model file")
        model_path = os.path.join("fixtures", "data_sets", "lda.csv")
        transfer, self.initial_dataset = data_catalog.create_dataset_from_file(context, org=TestData.test_org,
                                                                               file_path=model_path)

    @priority.low
    @pytest.mark.usefixtures("atk_virtualenv", "create_data_set")
    @pytest.mark.skip("We don't know how this should work")
    def test_create_transfer_from_atk_model_file(self):
        self.step("Get atk app from seedspace")
        atk_app = next((app for app in Application.cf_api_get_list_by_space(self.ref_space.guid) if app.name == "atk"),
                       None)
        if atk_app is None:
            raise AssertionError("Atk app not found in seedspace")

        self.step("Install atk client package in virtualenv")
        self.atk_virtualenv.create()
        self.atk_virtualenv.pip_install(ATKtools.get_atk_client_url(atk_app.urls[0]))

        self.step("Run atk create model script")
        ATKtools.check_uaac_token()
        atk_test_script_path = os.path.join("fixtures", "atk_test_scripts", "atk_create_model.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, atk_app.urls[0],
                                                      arguments={"--target_uri": self.initial_dataset.target_uri})

        self.step("Retrieve path to model file created by atk")
        hdfs_model_path = response.split("hdfs_model_path: ", 1)[1]

        self.step("Create dataset by providing retrieved model file path")
        _, ds = data_catalog.create_dataset_from_link(self.context, org=TestData.test_org, source=hdfs_model_path)
        self.assertEqual(ds.source_uri, hdfs_model_path)