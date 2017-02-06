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
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.configuration_provider.application import ApplicationConfigurationProvider
from modules.http_client import HttpMethod

logged_components = (TAP.space_shuttle_demo,)
pytestmark = [pytest.mark.components(TAP.space_shuttle_demo)]


@incremental
@priority.low
class TestSpaceShuttleDemo:
    SPACE_SHUTTLE_DEMO_APP_NAME = "space-shuttle-demo"
    SPACE_SHUTTLE_DEMO_CLIENT_NAME = "space-shuttle-demo-client"
    SPACE_SHUTTLE_GATEWAY = "space-shuttle-gateway"
    SPACE_SHUTTLE_SCORING_ENGINE = "space-shuttle-scoring-engine"
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
    @pytest.mark.bugs("DPNG-15302 500 Error while proxying request to service api, path /rest/services/")
    def test_5_check_if_client_sending_data_to_gateway(self, space_shuttle_client):
        application_log = space_shuttle_client.get_logs()
        assert self.check_that_logs_contain_client_data(application_log)

    @priority.low
    @pytest.mark.bugs("DPNG-15302 500 Error while proxying request to service api, path /rest/services/")
    def test_6_check_if_gateway_receiving_data_from_client(self, space_shuttle_gateway):
        service_log = space_shuttle_gateway.get_logs()
        assert self.check_that_logs_contain_client_data(service_log)

    def test_7_check_model_presence_in_scoring_engine(self):
        """
        <b>Description:</b>
        Checks if Scoring Engine can return information if provided data is anomaly basing on model.

        <b>Input data:</b>
        1. 9 digits representing lack of anomaly.

        <b>Expected results:</b>
        The application can return information if provided data is anomaly basing on model.

        <b>Steps:</b>
        1. Check if model is present in Scoring Engine.
        """
        step('Check if model is present in Scoring Engine')
        scoring_engine = ServiceInstance.get_by_name(self.SPACE_SHUTTLE_SCORING_ENGINE)
        client = HttpClientFactory.get(ApplicationConfigurationProvider.get(url=scoring_engine.url))
        response = client.request(method=HttpMethod.GET, params="data=1,1,1,1,1,1,1,1,1", path="v1/score")
        assert response == 1.0, "Scoring Engine model has changed"

    def test_8_space_shuttle_anomaly_detection(self, space_shuttle_application):
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
        step('Check if anomalies are detected')
        client = HttpClientFactory.get(ApplicationConfigurationProvider.get(url=space_shuttle_application.urls[0]))
        sample_data = client.request(method=HttpMethod.GET, path="rest/space-shuttle/chart", params={"groupBy": "1m",
                                                                                                     "since": "1h"})
        assert len(sample_data) > 0
