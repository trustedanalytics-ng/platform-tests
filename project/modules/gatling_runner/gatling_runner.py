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
from json import loads
from time import sleep
from urllib.request import urlretrieve

from modules.constants import LoggerType
from modules.tap_logger import get_logger
from .config import Config
from .gatling_ssh_connector import GatlingSshConnector
from .simulation.simulation_result import SimulationResult
from .gatling_runner_parameters import GatlingRunnerParameters
from .simulation.simulation_result_decoder import SimulationResultDecoder

logger = get_logger(LoggerType.GATLING_RUNNER)


class GatlingRunner(object):
    """Gatling performance tests runner."""

    LOG_WAIT = "Waiting for results ... Log file size: {} bytes"
    LOG_START = "Starting simulation: {}"
    LOG_DOWNLOAD = "Downloading package: {}"

    def __init__(self, parameters: GatlingRunnerParameters):
        self._parameters = parameters

    def run(self) -> SimulationResult:
        """Run gatling simulation tests and return results."""
        self._prepare_package()
        self._run_package()
        self._wait_for_results()
        return self._get_results()

    def _prepare_package(self):
        """Download gatling package if not exists."""
        if not os.path.isfile(Config.gatling_package_file_path()):
            logger.info(self.LOG_DOWNLOAD.format(Config.gatling_package_file_url()))
            urlretrieve(Config.gatling_package_file_url(), Config.gatling_package_file_path())

    def _run_package(self):
        """Execute gatling package."""
        logger.info(self.LOG_START.format(self._parameters.simulation_name.value))
        with self._connect() as c:
            self._parameters.execution_directory = c.start_simulation()

    def _wait_for_results(self):
        """Wait until results ready or exceeded trials number without log file size change."""
        log_size = 0
        trials_without_log_change = 0
        while not self._is_results_ready():
            current_log_size = self._get_log_size()
            if current_log_size > log_size:
                trials_without_log_change = 0
            else:
                trials_without_log_change += 1
            if trials_without_log_change > Config.number_of_trials_without_log_change():
                raise GatlingRunnerExceededNumberOfTrialsWithoutLogChangeException(self._parameters.log_file)
            log_size = current_log_size
            logger.info(self.LOG_WAIT.format(current_log_size))
            sleep(Config.TIME_BEFORE_NEXT_TRY)

    def _is_results_ready(self) -> bool:
        """Check if there is json file with results."""
        with self._connect() as c:
            return c.is_results_ready()

    def _get_log_size(self) -> int:
        """Return simulation log file size."""
        with self._connect() as c:
            return c.get_log_size()

    def _get_results(self) -> SimulationResult:
        """Return decoded results json file."""
        with self._connect() as c:
            results = c.get_results()
        return loads(results, cls=SimulationResultDecoder)

    def _connect(self):
        """Return gatling ssh connector."""
        return GatlingSshConnector(self._parameters)


class GatlingRunnerExceededNumberOfTrialsWithoutLogChangeException(Exception):
    def __init__(self, message=None):
        super().__init__("Execution log file: {}".format(message))
