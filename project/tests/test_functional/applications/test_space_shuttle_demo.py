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

from modules.constants import ServiceLabels, TapEntityState, TapComponent as TAP
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance
from retry import retry

logged_components = (TAP.space_shuttle_demo,)
pytestmark = [pytest.mark.components(TAP.space_shuttle_demo)]


@incremental
@priority.low
class TestSpaceShuttleDemo:
    SPACE_SHUTTLE_DEMO_APP_NAME = "space-shuttle-demo"
    SPACE_SHUTTLE_DEMO_CLIENT_NAME = "space-shuttle-demo-client"
    SPACE_SHUTTLE_GATEWAY = "space-shuttle-gateway"
    EXPECTED_BINDINGS = [ServiceLabels.GATEWAY, ServiceLabels.INFLUX_DB_088, ServiceLabels.SCORING_ENGINE]

    @pytest.fixture(scope="class")
    def space_shuttle_client(self):
        return Application.get_by_name(self.SPACE_SHUTTLE_DEMO_CLIENT_NAME)

    @pytest.fixture(scope="class")
    def space_shuttle_gateway(self):
        return ServiceInstance.get_by_name(self.SPACE_SHUTTLE_GATEWAY)

    def format_logs(self, logs_data):
        logs = list(logs_data.values())
        return "".join(logs).split("\n")

    def check_that_logs_contain_client_data(self, space_shuttle_data):
        FEATURE_VECTOR_MAX_LENGTH = 10
        TARGET_FOUND_MATCHING_VECTOR_COUNT = 9
        for log_item in self.format_logs(space_shuttle_data):
            feature_vector = log_item.split(", ")
            if len(feature_vector) == FEATURE_VECTOR_MAX_LENGTH:
                found_matching_vector_count = 0
                for feature_vector_value in feature_vector:
                    try:
                        float(feature_vector_value)
                        found_matching_vector_count += 1
                        if found_matching_vector_count == TARGET_FOUND_MATCHING_VECTOR_COUNT:
                            return True
                    except ValueError:
                        continue

    @priority.low
    def test_0_check_if_app_exist(self, space_shuttle_application):
        """
        <b>Description:</b>
        Checks if space-shuttle-demo application exists.

        <b>Input data:</b>
        1. space-shuttle-demo application

        <b>Expected results:</b>
        The application exists.

        <b>Steps:</b>
        1. Verify the application has correct name.
        """
        assert space_shuttle_application.name == self.SPACE_SHUTTLE_DEMO_APP_NAME

    @priority.low
    def test_1_check_if_app_bindings_exist(self, space_shuttle_application):
        """
        <b>Description:</b>
        Checks if space-shuttle-demo application has bindings.

        <b>Input data:</b>
        1. space-shuttle-demo application

        <b>Expected results:</b>
        The application has bindings.

        <b>Steps:</b>
        1. Verify the application has correct bindings.
        """
        app_binding = []

        for binding in space_shuttle_application.bindings:
            app_binding.append(ServiceInstance.get(service_id=binding["id"]).offering_label)

        assert sorted(app_binding) == sorted(self.EXPECTED_BINDINGS)

    @priority.low
    def test_2_check_if_app_running(self, space_shuttle_application):
        """
        <b>Description:</b>
        Checks if space-shuttle-demo application is running.

        <b>Input data:</b>
        1. space-shuttle-demo application

        <b>Expected results:</b>
        The application is running.

        <b>Steps:</b>
        1. Verify the application is running.
        """
        assert space_shuttle_application.state == TapEntityState.RUNNING

    @priority.low
    def test_3_check_if_app_exist(self, space_shuttle_client):
        assert space_shuttle_client.name == self.SPACE_SHUTTLE_DEMO_CLIENT_NAME

    @priority.low
    def test_4_check_if_client_running(self, space_shuttle_client):
        assert space_shuttle_client.state == TapEntityState.RUNNING

    @priority.low
    def test_5_check_if_client_sending_data_to_gateway(self, space_shuttle_client):
        application_log = space_shuttle_client.get_logs()
        assert self.check_that_logs_contain_client_data(application_log)

    @priority.low
    def test_6_check_if_gateway_receiving_data_from_client(self, space_shuttle_gateway):
        service_log = space_shuttle_gateway.get_logs()
        assert self.check_that_logs_contain_client_data(service_log)

    @pytest.mark.skip(reason="DPNG-9278 [space shuttle demo] Enable usage os Scoring Engine")
    def test_2_check_app_model_dataset_title_and_uri(self, core_org):
        """
        <b>Description:</b>
        Checks if space-shuttle-demo application has correct dataset title and uri.

        <b>Input data:</b>
        1. Organization

        <b>Expected results:</b>
        The application has correct a dataset and a title.

        <b>Steps:</b>
        1. Verify the title.
        2. Verify the uri.
        """
        step('Check model title is as expected')
        dataset_list = DataSet.api_get_list(org_guid_list=[core_org.guid])
        model = next((d for d in dataset_list if d.title == self.MODEL_TITLE), None)
        assert model is not None, 'Model dataset is not present'
        step('Check model uri is as expected')
        assert self.MODEL_SOURCE_FILE_NAME == model.source_uri, 'Model source file name is not as expected'

    @pytest.mark.skip(reason="DPNG-9278 [space shuttle demo] Enable usage os Scoring Engine")
    def test_3_space_shuttle_anomaly_detection(self, space_shuttle_demo_app, space_shuttle_client_app):
        """
        <b>Description:</b>
        Checks if space-shuttle-demo application anomalies are detected correctly.

        <b>Input data:</b>
        1. space-shuttle-demo application
        2. space-shuttle client

        <b>Expected results:</b>
        Anomalies are detected correctly.

        <b>Steps:</b>
        1. Post samples.
        2. Verify the anomalies.
        """
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
