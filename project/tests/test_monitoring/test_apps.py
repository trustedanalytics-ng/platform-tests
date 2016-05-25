#
# Copyright (c) 2015-2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytest

from modules.api_client import PlatformApiClient
from modules.tap_logger import step
from modules.tap_object_model import Application


class TestAppMonitoring(object):

    TESTED_APP_NAMES = {
        "das",
        "metrics-provider",
        "router-metrics-provider",
        "user-management",
    }

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def get_apps(cls, core_space):
        cls.platform_apps = Application.api_get_list(core_space.guid)

    def test_all_required_apps_are_present_on_platform(self):
        step("Check that all expected apps are present on the Platform")
        app_names = {a.name for a in self.platform_apps}
        missing_apps = self.TESTED_APP_NAMES - app_names
        assert missing_apps == set(), "Apps missing on the Platform"

    def test_all_required_apps_are_running_on_platform(self):
        step("Check that all expected apps have running instances on the Platform")
        apps_not_running = {a.name for a in self.platform_apps if a.name in self.TESTED_APP_NAMES and not a.is_running}
        assert apps_not_running == set(), "Apps with no running instances on the Platform"

    def test_app_endpoints(self):
        step("Retrieve apps, and services on the Platform")
        tested_apps = {a for a in self.platform_apps if a.name in self.TESTED_APP_NAMES}
        step("Send GET /health request to apps: {}".format(self.TESTED_APP_NAMES))
        client = PlatformApiClient.get_admin_client("app")
        for app in tested_apps:
            step("Testing app with name: {}".format(app.name))
            client.request(method="GET", app_name=app.urls[0].split(".")[0], endpoint="health")
