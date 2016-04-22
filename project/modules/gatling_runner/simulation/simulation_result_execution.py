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


class SimulationResultExecution(object):
    """Simulation request executions results."""

    COMPARABLE_ATTRIBUTES = ("total", "ok", "ko")

    def __init__(self, total=None, ok=None, ko=None):
        self.__total = total
        self.__ok = ok
        self.__ko = ko

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    @property
    def total(self):
        """Total number of requests."""
        return self.__total

    @property
    def ok(self):
        """Number of requests without errors."""
        return self.__ok

    @property
    def ko(self):
        """Total number of requests with errors."""
        return self.__ko
