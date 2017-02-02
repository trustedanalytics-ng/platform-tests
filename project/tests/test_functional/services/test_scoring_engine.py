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
import requests

from modules.constants import ScoringEngineHttpStatus, TapComponent as TAP, ServiceLabels, ServicePlan
from modules.markers import incremental, long, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance

logged_components = (TAP.scoring_engine, TAP.service_catalog, TAP.das, TAP.downloader,
                     TAP.metadata_parser)
pytestmark = [pytest.mark.components(TAP.scoring_engine, TAP.service_catalog)]


@long
@priority.high
@incremental
@pytest.mark.sample_apps_test
class TestScoringEngineInstance:
    expected_se_bindings = [ServiceLabels.KERBEROS, ServiceLabels.HDFS]

    @pytest.fixture(scope="class")
    def se_instance(self, class_context):
        step("Create scoring engine instance")
        instance = ServiceInstance.create_with_name(
            context=class_context,
            offering_label=ServiceLabels.SCORING_ENGINE,
            plan_name=ServicePlan.SINGLE
        )
        step("Check that scoring engine instance is runnning")
        instance.ensure_running()
        return instance

    def test_0_create_instance(self, se_instance):
        """
        <b>Description:</b>
        Check creation of scoring engine instance.

        <b>Input data:</b>
        1. organization id

        <b>Expected results:</b>
        Test passes if scoring engine instance is created successfully.

        <b>Steps:</b>
        1. Create scoring engine instance.
        2. Check that created instance is present on instances list.
        """
        step("Check instance is on the instance list")
        instances_list = ServiceInstance.get_list()
        assert se_instance in instances_list, "Scoring Engine was not found on the instance list"

    def test_1_upload_mar_model(self, se_instance, jumpbox_model_file):
        """
        <b>Description:</b>
        Upload model to scoring engine application.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if scoring engine application returns correct response.

        <b>Steps:</b>
        1. Send request with model to scoring engine application.
        2. Check scoring engine application response.
        """
        step("Send request with model to scoring engine application")
        file = open(jumpbox_model_file, 'rb')
        url = "{}/uploadMarBytes".format(se_instance.url)
        headers = {"Accept": "text/plain", "Content-Types": "text/plain; charset=UTF-8"}
        response = requests.post(url, data=file, headers=headers)
        assert ScoringEngineHttpStatus.MSG_MODEL_SUCCESSFULLY_UPLOADED in response.text

    def test_2_check_request_to_se_application(self, se_instance):
        """
        <b>Description:</b>
        Send request to scoring engine application.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if scoring engine application returns correct response.

        <b>Steps:</b>
        1. Check that Scoring Engine app responds to an HTTP request
        """
        step("Check that Scoring Engine app responds to an HTTP request")
        url = "{}/v1/score?data=1,2,3,4,5,6,7,8,9".format(se_instance.url)
        headers = {"Accept": "text/plain", "Content-Types": "text/plain; charset=UTF-8"}
        response = requests.post(url, data="", headers=headers)
        assert response.text == ScoringEngineHttpStatus.MSG_SCORING_ENGINE_RESULT, "Scoring engine response was wrong"

    def test_3_delete_se_instance(self, se_instance):
        """
        <b>Description:</b>
        Check that scoring engine instance can be deleted.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if scoring engine instance is successfully deleted.

        <b>Steps:</b>
        1. Stop scoring engine instance.
        2. Check that scoring engine instance was stopped.
        3. Delete scoring engine instance.
        4. Check that scoring engine instance was successfully deleted.
        """
        step("Stop service instance")
        se_instance.stop()
        step("Check that scoring engine instance was stopped.")
        se_instance.ensure_stopped()
        step("Delete scoring engine instance.")
        se_instance.delete()
        step("Check that scoring engine instance was deleted.")
        se_instance.ensure_deleted()
        instances = ServiceInstance.get_list()
        assert se_instance not in instances, "Scoring engine instance was not deleted"
