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

from modules.api_client import PlatformApiClient
from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import Application, Organization


class AppMonitoring(TapTestCase):

    TESTED_APP_NAMES = {"das", "metrics-provider", "router-metrics-provider", "user-management"}

    @classmethod
    def setUpClass(cls):
        ref_space_guid = Organization.get_ref_org_and_space()[1].guid
        cls.platform_apps = Application.api_get_list(ref_space_guid)

    def test_all_required_apps_are_present_on_platform(self):
        self.step("Check that all expected apps are present on the Platform")
        app_names = {a.name for a in self.platform_apps}
        missing_apps = self.TESTED_APP_NAMES - app_names
        self.assertEqual(missing_apps, set(), "Apps missing on the Platform")

    def test_all_required_apps_are_running_on_platform(self):
        self.step("Check that all expected apps have running instances on the Platform")
        apps_not_running = {a.name for a in self.platform_apps if a.name in self.TESTED_APP_NAMES and not a.is_running}
        self.assertEqual(apps_not_running, set(), "Apps with no running instances on the Platform")

    def test_app_endpoints(self):
        self.step("Retrieve apps, and services on the Platform")
        tested_apps = {a for a in self.platform_apps if a.name in self.TESTED_APP_NAMES}
        self.step("Send GET /health request to apps: {}".format(self.TESTED_APP_NAMES))
        client = PlatformApiClient.get_admin_client("app")
        for app in tested_apps:
            with self.subTest(app=app.name):
                client.request(method="GET", app_name=app.urls[0].split(".")[0], endpoint="health")
