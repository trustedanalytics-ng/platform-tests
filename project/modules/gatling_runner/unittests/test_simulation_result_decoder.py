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

import json

from modules.gatling_runner.unittests.package_test_case import PackageTestCase
from modules.gatling_runner.simulation.simulation_result_execution import SimulationResultExecution
from modules.gatling_runner.simulation.simulation_result_group import SimulationResultGroup
from modules.gatling_runner.simulation.simulation_result_decoder import SimulationResultDecoder, \
    SimulationResultDecoderInvalidJsonException


class TestSimulationResultDecoder(PackageTestCase):
    """Unit: SimulationResultDecoder."""

    def test_decode_should_raise_exception(self):
        # given
        invalid_json = "{}"

        # when
        self.assertRaisesRegex(
            SimulationResultDecoderInvalidJsonException,
            "Provided json is not valid.",
            json.loads,
            invalid_json,
            cls=SimulationResultDecoder
        )

    def test_decode_should_return_result_object(self):
        # given
        json_string = self._load_fixture("global_stats.json")

        # when
        result = json.loads(json_string, cls=SimulationResultDecoder)

        # then
        self.assertEqual(
            result.number_of_requests,
            SimulationResultExecution(total=13, ok=9, ko=4)
        )
        self.assertEqual(
            result.min_response_time,
            SimulationResultExecution(total=0, ok=149, ko=0)
        )
        self.assertEqual(
            result.max_response_time,
            SimulationResultExecution(total=834, ok=834, ko=0)
        )
        self.assertEqual(
            result.mean_response_time,
            SimulationResultExecution(total=213, ok=308, ko=0)
        )
        self.assertEqual(
            result.mean_number_of_requests_per_second,
            SimulationResultExecution(
                total=4.120443740095087,
                ok=2.8526148969889067,
                ko=1.2678288431061808
            )
        )
        self.assertEqual(
            result.standard_deviation,
            SimulationResultExecution(total=225, ok=209, ko=0)
        )
        self.assertEqual(
            result.percentiles1,
            SimulationResultExecution(total=158, ok=209, ko=0)
        )
        self.assertEqual(
            result.percentiles2,
            SimulationResultExecution(total=343, ok=373, ko=0)
        )
        self.assertEqual(
            result.percentiles3,
            SimulationResultExecution(total=573, ok=660, ko=0)
        )
        self.assertEqual(
            result.percentiles4,
            SimulationResultExecution(total=781, ok=799, ko=0)
        )
        self.assertEqual(
            result.number_of_fast_requests,
            SimulationResultGroup(
                name="t < 800 ms",
                count=8,
                percentage=62
            )
        )
        self.assertEqual(
            result.number_of_average_requests,
            SimulationResultGroup(
                name="800 ms < t < 1200 ms",
                count=1,
                percentage=8
            )
        )
        self.assertEqual(
            result.number_of_slow_requests,
            SimulationResultGroup(
                name="t > 1200 ms",
                count=0,
                percentage=0
            )
        )
        self.assertEqual(
            result.number_of_failed_requests,
            SimulationResultGroup(
                name="failed",
                count=4,
                percentage=31
            )
        )
