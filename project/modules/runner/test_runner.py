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

from .custom_runners import TapTestRunner, DBTestRunner
from configuration import config

UNITTEST_RUNNER_VERBOSITY = 3


class TestRunner(object):

    def __new__(cls):
        # select test runner class depending on database configuration
        if config.CONFIG.get("database_url") is None:
            return TapTestRunner(verbosity=UNITTEST_RUNNER_VERBOSITY)
        else:
            return DBTestRunner(verbosity=UNITTEST_RUNNER_VERBOSITY)

