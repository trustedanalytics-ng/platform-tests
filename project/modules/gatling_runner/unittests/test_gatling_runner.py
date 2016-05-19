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

import mock

from modules.gatling_runner.unittests.package_test_case import PackageTestCase
from modules.gatling_runner.gatling_runner import GatlingRunner, \
    GatlingRunnerExceededNumberOfTrialsWithoutLogChangeException
from modules.gatling_runner.simulation.simulation_result import SimulationResult
from modules.gatling_runner.simulation.simulation_name import SimulationName
from modules.gatling_runner.gatling_runner_parameters import GatlingRunnerParameters
from modules.gatling_runner.gatling_ssh_connector import GatlingSshConnectorException


class GatlingSshConnectorMock(object):
    """GatlingSshConnector mock."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def start_simulation(self):
        return "execution_directory"

    def is_results_ready(self):
        return True

    def get_log_size(self):
        return 0


class TestGatlingRunner(PackageTestCase):
    """Unit: GatlingRunner."""

    def setUp(self):
        patcher = mock.patch("os.path.isfile")
        self.mock_isfile_call = patcher.start()
        self.mock_isfile_call.return_value = True
        self.addCleanup(patcher.stop)
        self._parameters = GatlingRunnerParameters(
            simulation_name=SimulationName.LOAD_RESOURCES,
            platform="test.platform",
            organization="test.organization",
            space="test.space",
            username="test.username",
            password="test.password",
            proxy="test.proxy",
            proxy_http_port=1,
            proxy_https_port=2,
            users=3,
            users_at_once=4,
            ramp=5,
            duration=6,
            repeat=7
        )
        self._gatling_runner = GatlingRunner(self._parameters)

    @mock.patch("modules.gatling_runner.gatling_ssh_connector.GatlingSshConnector._connect")
    def test_run_should_return_ssh_connection_exception(self, connect_mock):
        # given
        connect_mock.side_effect = GatlingSshConnectorException

        # when
        self.assertRaisesRegex(
            GatlingSshConnectorException,
            "Gatling connector ssh connection problem.",
            self._gatling_runner.run
        )

    @mock.patch('modules.gatling_runner.config.Config.TIME_BEFORE_NEXT_TRY', 0)
    @mock.patch('modules.gatling_runner.config.Config.NUMBER_OF_TRIALS_WITHOUT_LOG_CHANGE', 1)
    @mock.patch("modules.gatling_runner.gatling_runner.GatlingRunner._connect")
    def test_run_should_return_exceeded_number_of_trials_without_log_change_exception(self, connect_mock):
        # given
        class ConnectorMock(GatlingSshConnectorMock):
            def is_results_ready(self):
                return False

        connect_mock.return_value = ConnectorMock()

        # when
        self.assertRaises(GatlingRunnerExceededNumberOfTrialsWithoutLogChangeException, self._gatling_runner.run)

    @mock.patch("modules.gatling_runner.gatling_runner.GatlingRunner._connect")
    def test_run_should_return_results(self, connect_mock):
        # given
        json_string = self._load_fixture("global_stats.json")

        class ConnectorMock(GatlingSshConnectorMock):
            def get_results(self):
                return json_string

        connect_mock.return_value = ConnectorMock()

        # when
        result = self._gatling_runner.run()

        # then
        self.assertIsInstance(result, SimulationResult, "Invalid result instance.")
