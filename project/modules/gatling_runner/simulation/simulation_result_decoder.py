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

from json import JSONDecoder
from json.decoder import WHITESPACE

from .simulation_result import SimulationResult
from .simulation_result_group import SimulationResultGroup
from .simulation_result_execution import SimulationResultExecution


class SimulationResultDecoder(JSONDecoder):
    """Gatling simulation results decoder."""

    def decode(self, s, _w=WHITESPACE.match):
        """Return the SimulationResult representation of JSON."""
        obj = super().decode(s)
        try:
            return SimulationResult(
                number_of_requests=self._execution(obj["numberOfRequests"]),
                min_response_time=self._execution(obj["minResponseTime"]),
                max_response_time=self._execution(obj["maxResponseTime"]),
                mean_response_time=self._execution(obj["meanResponseTime"]),
                standard_deviation=self._execution(obj["standardDeviation"]),
                percentiles1=self._execution(obj["percentiles1"]),
                percentiles2=self._execution(obj["percentiles2"]),
                percentiles3=self._execution(obj["percentiles3"]),
                percentiles4=self._execution(obj["percentiles4"]),
                group1=self._group(obj["group1"]),
                group2=self._group(obj["group2"]),
                group3=self._group(obj["group3"]),
                group4=self._group(obj["group4"]),
                mean_number_of_requests_per_second=self._execution(obj["meanNumberOfRequestsPerSecond"]),
            )
        except:
            raise SimulationResultDecoderInvalidJsonException

    @staticmethod
    def _execution(map_item):
        """Return SimulationResultExecution representation of JSON."""
        return SimulationResultExecution(
            total=map_item["total"],
            ok=map_item["ok"],
            ko=map_item["ko"]
        )

    @staticmethod
    def _group(map_item):
        """Return SimulationResultGroup representation of JSON."""
        return SimulationResultGroup(
            name=map_item["name"],
            count=map_item["count"],
            percentage=map_item["percentage"]
        )


class SimulationResultDecoderInvalidJsonException(Exception):
    def __init__(self):
        super().__init__("Provided json is not valid.")
