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

project_path = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.append(project_path)

from modules.constants.project_paths import Path
from stress_tests.tap_locust import tap_locust


class UserBehaviorUserManagement(TaskSet):
    SMOKE_TESTS_MODULE = os.path.join(Path.test_directories["test_smoke"], "test_functional.py")

    @task(1)
    def create_delete_user(self):
        self.client.run(self.locust, self.SMOKE_TESTS_MODULE, "test_add_new_user_to_and_delete_from_org")

    @task(1)
    def onboarding(self):
        self.client.run(self.locust, self.SMOKE_TESTS_MODULE, "test_onboarding")

    @task(1)
    def login(self):
        self.client.run(self.locust, self.SMOKE_TESTS_MODULE, "test_login")


class UserManagementUser(tap_locust.TapLocust):
    task_set = UserBehaviorUserManagement
