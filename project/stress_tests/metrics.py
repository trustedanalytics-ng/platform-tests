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

from locust import TaskSet, task

from modules.constants import Path
from stress_tests.tap_locust import tap_locust
from stress_tests.tap_locust.task_set_utils import PytestSelector


class UserBehaviorMetrics(TaskSet):
    TEST_MODULE_PATH = os.path.join(Path.test_directories["stress_scenarios"], "test_scenarios.py")
    TEST_CLASS_NAME = "TestMetrics"

    @task(1)
    def get_org_metrics(self):
        pytest_selector = PytestSelector(self.TEST_MODULE_PATH, self.TEST_CLASS_NAME, "test_get_org_metrics")
        self.client.run(pytest_selector)


class MetricsUser(tap_locust.TapLocust):
    task_set = UserBehaviorMetrics
