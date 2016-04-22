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

import unittest

from configuration.config import CONFIG
from modules.gatling_runner.gatling_runner import GatlingRunner
from modules.gatling_runner.gatling_runner_parameters import GatlingRunnerParameters
from modules.gatling_runner.simulation.simulation_name import SimulationName
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.decorators import components, priority
from modules.constants import TapComponent as Tap


@log_components()
@components(Tap.data_catalog, Tap.das, Tap.hdfs_downloader, Tap.metadata_parser)
class DataCatalogPerformanceTest(unittest.TestCase):
    """Data catalog gatling performance tests."""

    @priority.low
    def test_add_data_set(self):
        """Test adding data set to data catalog."""
        parameters = GatlingRunnerParameters(
            simulation_name=SimulationName.ADD_DATA_SET.value,
            platform=CONFIG["domain"],
            organization=CONFIG["ref_org_name"],
            space=CONFIG["ref_space_name"],
            username=CONFIG["admin_username"],
            password=CONFIG["admin_password"],
            users_at_once=10,
        )
        gatling_runner = GatlingRunner(parameters)
        result = gatling_runner.run()
        self.assertTrue(result.number_of_failed_requests.name < 10, "Percentage of failed requests is to high.")
        self.assertTrue(result.number_of_slow_requests.percentage < 20, "Percentage of slow requests is to high.")
