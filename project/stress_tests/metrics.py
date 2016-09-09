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

from locust import TaskSet, task

import os
import sys

# workaround allowing import from framework modules
from modules.constants import Path

project_path = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.append(project_path)

from stress_tests.tap_locust import tap_locust


class UserBehaviorMetrics(TaskSet):
    TEST_MODULE_PATH = os.path.join(Path.test_directories["stress_scenarios"], "test_scenarios.py")
    TEST_CLASS_NAME = "TestMetrics"

    @task(1)
    def get_org_metrics(self):
        self.client.run(self.locust, self.TEST_MODULE_PATH, self.TEST_CLASS_NAME, "test_get_org_metrics")


class MetricsUser(tap_locust.TapLocust):
    task_set = UserBehaviorMetrics
