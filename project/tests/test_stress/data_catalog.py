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
import sys

from locust import TaskSet, task

sys.path.append(os.getcwd())

from modules.constants.project_paths import Path
from stress_tests.tap_locust import tap_locust
from stress_tests.tap_locust.task_set_utils import PytestSelector


class UserBehaviorDataCatalog(TaskSet):
    SMOKE_TESTS_MODULE = os.path.join(Path.test_directories["test_smoke"], "test_functional.py")

    @task(1)
    def add_and_delete_from_link(self):
        pytest_selector = PytestSelector(module_path=self.SMOKE_TESTS_MODULE,
                                         test_name="test_add_and_delete_transfer_from_link")
        self.client.run(pytest_selector)

    @task(1)
    def add_and_delete_from_file(self):
        pytest_selector = PytestSelector(module_path=self.SMOKE_TESTS_MODULE,
                                         test_name="test_add_and_delete_transfer_from_file")
        self.client.run(pytest_selector)


class DataCatalogUser(tap_locust.TapLocust):
    task_set = UserBehaviorDataCatalog
