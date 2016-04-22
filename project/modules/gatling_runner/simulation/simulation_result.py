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

from .simulation_result_group import SimulationResultGroup
from .simulation_result_execution import SimulationResultExecution


class SimulationResult(object):
    """Gatling simulation results object."""

    def __init__(self, number_of_requests=None, min_response_time=None, max_response_time=None, mean_response_time=None,
                 standard_deviation=None, percentiles1=None, percentiles2=None, percentiles3=None, percentiles4=None,
                 group1=None, group2=None, group3=None, group4=None, mean_number_of_requests_per_second=None):
        self.__number_of_requests = number_of_requests
        self.__min_response_time = min_response_time
        self.__max_response_time = max_response_time
        self.__mean_response_time = mean_response_time
        self.__mean_number_of_requests_per_second = mean_number_of_requests_per_second
        self.__standard_deviation = standard_deviation
        self.__percentiles1 = percentiles1
        self.__percentiles2 = percentiles2
        self.__percentiles3 = percentiles3
        self.__percentiles4 = percentiles4
        self.__group1 = group1
        self.__group2 = group2
        self.__group3 = group3
        self.__group4 = group4

    @property
    def number_of_requests(self) -> SimulationResultExecution:
        """Number of requests."""
        return self.__number_of_requests

    @property
    def min_response_time(self) -> SimulationResultExecution:
        """Minimal response time."""
        return self.__min_response_time

    @property
    def max_response_time(self) -> SimulationResultExecution:
        """Maximal response time."""
        return self.__max_response_time

    @property
    def mean_response_time(self) -> SimulationResultExecution:
        """Mean response time."""
        return self.__mean_response_time

    @property
    def mean_number_of_requests_per_second(self) -> SimulationResultExecution:
        """Mean number of requests per second."""
        return self.__mean_number_of_requests_per_second

    @property
    def standard_deviation(self) -> SimulationResultExecution:
        """Standard deviation."""
        return self.__standard_deviation

    @property
    def percentiles1(self) -> SimulationResultExecution:
        """Percentiles group one."""
        return self.__percentiles1

    @property
    def percentiles2(self) -> SimulationResultExecution:
        """Percentiles group two."""
        return self.__percentiles2

    @property
    def percentiles3(self) -> SimulationResultExecution:
        """Percentiles group three."""
        return self.__percentiles3

    @property
    def percentiles4(self) -> SimulationResultExecution:
        """Percentiles group four."""
        return self.__percentiles4

    @property
    def number_of_fast_requests(self) -> SimulationResultGroup:
        """Request with time: t < 800 ms."""
        return self.__group1

    @property
    def number_of_average_requests(self) -> SimulationResultGroup:
        """Request with time: 800 ms < t < 1200 ms."""
        return self.__group2

    @property
    def number_of_slow_requests(self) -> SimulationResultGroup:
        """Request with time: t > 1200 ms."""
        return self.__group3

    @property
    def number_of_failed_requests(self) -> SimulationResultGroup:
        """Request with status failed."""
        return self.__group4
