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
from datetime import datetime

import pytest

from modules.constants import ServiceLabels, TapComponent as TAP, TapGitHub
from modules.http_calls.platform import space_shuttle_demo
from modules.markers import incremental, priority
from modules.platform_version import get_appstack_yml
from modules.tap_logger import step
from modules.tap_object_model import Application, DataSet, Binding, ServiceInstance

logged_components = (TAP.space_shuttle_demo,)
pytestmark = [pytest.mark.components(TAP.space_shuttle_demo)]


@incremental
@priority.low
@pytest.mark.skip("DPNG-8659: Adjust Space-shuttle & mqtt: functional tests")
class TestSpaceShuttleDemo:
    MODEL_TITLE = "model"
    MODEL_SOURCE_FILE_NAME = "space-shuttle-model.tar"
    SPACE_SHUTTLE_APP_NAME = "space_shuttle_client"
    expected_bindings = [ServiceLabels.INFLUX_DB, ServiceLabels.GATEWAY, ServiceLabels.SCORING_ENGINE,
                         ServiceLabels.ZOOKEEPER]

    @pytest.fixture(scope="class")
    def space_shuttle_demo_app(self, core_space):
        space_shuttle_demo_app = next((app for app in Application.api_get_list(core_space.guid)
                                       if TAP.space_shuttle_demo == app.name), None)
        return space_shuttle_demo_app

    @pytest.fixture(scope="class")
    def space_shuttle_client_app(self, core_space):
        space_shuttle_client_app = next((app for app in Application.api_get_list(core_space.guid)
                                         if self.SPACE_SHUTTLE_APP_NAME == app.name), None)
        return space_shuttle_client_app

    def test_0_check_if_app_is_on_appstack_and_is_deployed_and_is_running(self, space_shuttle_demo_app):
        step("Try to get application from appstack.yml to check if the application should be deployed")
        space_shuttle_demo_yml = next((app for app in get_appstack_yml(TapGitHub.intel_data)["apps"]
                                       if app["name"] == TAP.space_shuttle_demo), None)
        assert space_shuttle_demo_yml is not None, '{} is not on appstack.yml list'.format(TAP.space_shuttle_demo)
        step('Check the app is deployed')
        assert space_shuttle_demo_app is not None, '{} is not deployed'.format(TAP.space_shuttle_demo)
        step('Check the app is running')
        assert space_shuttle_demo_app.is_running, 'space shuttle is not running'

    def test_1_check_if_app_has_correct_bindings(self, core_space, space_shuttle_demo_app):
        step('Check required services are correctly bound')
        instances = ServiceInstance.api_get_list(core_space.guid)
        bindings = Binding.api_get_list(app_guid=space_shuttle_demo_app.guid)
        binding_guids = [b.service_instance_guid for b in bindings]
        bound_instance_labels = [i.service_label for i in instances if i.guid in binding_guids]
        assert sorted(self.expected_bindings) == sorted(bound_instance_labels)

    def test_2_check_app_model_dataset_title_and_uri(self, core_org):
        step('Check model title is as expected')
        dataset_list = DataSet.api_get_list(org_guid_list=[core_org.guid])
        model = next((d for d in dataset_list if d.title == self.MODEL_TITLE), None)
        assert model is not None, 'Model dataset is not present'
        step('Check model uri is as expected')
        assert self.MODEL_SOURCE_FILE_NAME == model.source_uri, 'Model source file name is not as expected'

    def test_3_space_shuttle_anomaly_detection(self, space_shuttle_demo_app, space_shuttle_client_app):
        step('Check that anomalies are detected correctly')
        now = time.time()
        an_hour_ago = now - 3600
        interval = '60m'
        step("Check how long the client works")
        current_utc_date_and_time = datetime.utcnow()
        space_shuttle_client_package_updated_at_utc = datetime.strptime(space_shuttle_client_app.api_get_summary()
                                                                        ["package_updated_at"], '%Y-%m-%dT%H:%M:%SZ')
        space_shuttle_client_up_time = current_utc_date_and_time - space_shuttle_client_package_updated_at_utc
        space_shuttle_client_up_time = space_shuttle_client_up_time.seconds
        '''
        Test may fail if application was started less than hour before.
        Time in Application.api_get_summary["package_updated_at"] is UTC
        '''
        interval_start = str(int(an_hour_ago * 1000))
        step("Get samples data")
        samples_data = space_shuttle_demo.post_samples(space_shuttle_demo_app, interval, interval_start)
        step("If up time is less than 1h, check that any data are returned")
        if space_shuttle_client_up_time < 3600:
            assert len(samples_data) > 0
        step("If up time is more than 1h, check if anomalies are present for 90% of time")
        if space_shuttle_client_up_time > 3600:
            percent_correct = 90
        else:
            percent_correct = 70
        '''
        There are 10 classes of anomalies. The correct one is class=5. Test checks the quality of algorithm
        by comparing the most populated anomaly class (probably 5) against the sum of all anomalies detected.
        percent_correct value (70) is chosen to pass most of the tests (it is not critical test)
        '''
        quantity_of_class_anomalies = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for _, anomaly in samples_data.items():
            anomaly_class = int(anomaly[1])
            quantity_of_class_anomalies[anomaly_class] += 1
        assert max(quantity_of_class_anomalies) * 100 / sum(quantity_of_class_anomalies) > percent_correct
