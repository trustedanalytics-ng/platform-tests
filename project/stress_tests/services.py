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

from locust import TaskSet

project_path = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.append(project_path)

from modules.constants.project_paths import Path
from stress_tests.tap_locust import tap_locust
from stress_tests.tap_locust.task_set_utils import tasks_from_parametrized_test, PytestSelector
from tap_component_config import offerings_as_parameters


class UserBehaviorCreatingMarketplaceServices(TaskSet):
    SMOKE_TESTS_MODULE = os.path.join(Path.test_directories["test_smoke"], "test_functional.py")
    TEST_NAME = "test_create_and_delete_marketplace_service_instances"

    def on_start(self):
        pytest_selector = PytestSelector(module_path=self.SMOKE_TESTS_MODULE, test_name=self.TEST_NAME)
        self.tasks = tasks_from_parametrized_test(pytest_selector, offerings_as_parameters)


class MarketplaceUser(tap_locust.TapLocust):
    task_set = UserBehaviorCreatingMarketplaceServices
