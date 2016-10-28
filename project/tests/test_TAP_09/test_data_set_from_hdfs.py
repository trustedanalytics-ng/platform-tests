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

import pytest

from modules.constants import TapComponent as TAP
from modules.tap_logger import step
from modules.markers import priority
from modules.service_tools.atk import ATKtools
from modules.tap_object_model import Application
from modules.tap_object_model.flows import data_catalog


logged_components = (TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.data_catalog, TAP.das, TAP.downloader, TAP.metadata_parser)]


class TestDataSetFromHdfs(object):

    @classmethod
    @pytest.fixture(scope="function")
    def atk_virtualenv(cls, request, test_org):
        atk_virtualenv = ATKtools("atk_virtualenv")
        request.addfinalizer(lambda: atk_virtualenv.teardown(org=test_org))

    @pytest.fixture(scope="function")
    def initial_dataset(self, request, context, test_org):
        step("Create data set from model file")
        model_path = os.path.join("fixtures", "data_sets", "lda.csv")
        _, initial_dataset = data_catalog.create_dataset_from_file(context, org_guid=test_org.guid,
                                                                   file_path=model_path)
        return initial_dataset

    @priority.low
    @pytest.mark.usefixtures("atk_virtualenv")
    @pytest.mark.skip("We don't know how this should work")
    def test_create_transfer_from_atk_model_file(self, context, test_org, atk_virtualenv, initial_dataset):
        step("Get atk app")
        atk_app = next((app for app in Application.get_list() if app.name == "atk"), None)
        if atk_app is None:
            raise AssertionError("Atk app not found")

        step("Install atk client package in virtualenv")
        atk_virtualenv.create()
        atk_virtualenv.pip_install(ATKtools.get_atk_client_url(atk_app.urls[0]))

        step("Run atk create model script")
        atk_test_script_path = os.path.join("fixtures", "atk_test_scripts", "atk_create_model.py")
        response = atk_virtualenv.run_atk_script(atk_test_script_path, atk_app.urls[0],
                                                 arguments={"--target_uri": initial_dataset.target_uri})

        step("Retrieve path to model file created by atk")
        hdfs_model_path = response.split("hdfs_model_path: ", 1)[1]

        step("Create dataset by providing retrieved model file path")
        _, ds = data_catalog.create_dataset_from_link(context, org_guid=test_org.guid, source=hdfs_model_path)
        assert ds.source_uri == hdfs_model_path
