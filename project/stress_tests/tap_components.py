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

from locust import TaskSet, task, events

# sys.stderr.flush = lambda: None
# sys.stdout.flush = lambda: None
# sys.stdout.isatty = lambda: False

from modules.ssh_lib import JumpTunnel
from stress_tests.tap_locust import tap_locust

from modules.constants.project_paths import Path


# One tunnel is a bottleneck. For tests which require tunneling, a TunnelPool will need to be implemented
JUMP_TUNNEL = JumpTunnel()


class UserBehaviorImageFactory(TaskSet):
    TEST_MODULE_PATH = os.path.join(Path.test_directories["stress_scenarios"], "test_scenarios.py")
    TEST_CLASS_NAME = "TestImageFactory"

    @task(1)
    def get_image_factory_catalog(self):
        # self.client.run(self.locust, self.TEST_MODULE_PATH, self.TEST_CLASS_NAME, "test_get_catalog")
        print("Task")


class TAPComponentsUser(tap_locust.TapLocust):
    task_set = UserBehaviorImageFactory

    def __init__(self):
        super().__init__()
        events.quitting += JUMP_TUNNEL.close
