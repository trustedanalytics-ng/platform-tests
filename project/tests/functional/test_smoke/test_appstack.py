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

from modules.constants import ServiceLabels, TapGitHub
from modules.api_client import AppClient
from modules.exceptions import UnexpectedResponseError
from modules.platform_version import get_appstack_yml
from modules.runner.tap_test_case import TapTestCase
from modules.markers import long, priority
from modules.tap_logger import get_logger
from modules.tap_object_model import Application, ServiceBroker, ServiceInstance, Upsi


logger = get_logger(__name__)


@priority.high
class TrustedAnalyticsSmokeTest(TapTestCase):
    EXCLUDED_APP_NAMES = {ServiceLabels.ATK}
    # Gateway exposes all sensitive endpoints (request returns http status 200)
    SENSITIVE_ENDPOINTS_EXCLUDED_APPS = {ServiceLabels.GATEWAY}

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def expected_appstack(cls):
        cls.step("Retrieve content of appstack.yml file")
        appstack_yml = get_appstack_yml(TapGitHub.intel_data)
        cls.step("Retrieve expected app, service, and broker names from the file")

        def should_be_started(app_info):
            params = app_info.get("push_options", {}).get("params", "")
            return "--no-start" not in params

        cls.expected_app_names = {app_info["name"] for app_info in appstack_yml["apps"] if should_be_started(app_info)}
        cls.expected_upsi_names = {app_info["name"] for app_info in appstack_yml["user_provided_services"]}
        cls.expected_broker_names = {app_info["name"] for app_info in appstack_yml["brokers"]}

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def appstack(cls, core_space):
        cls.step("Retrieve apps, services, and brokers present in cf")
        cls.cf_apps = Application.cf_api_get_list_by_space(core_space.guid)
        cls.cf_upsi = [s for s in Upsi.cf_api_get_list() if s.space_guid == core_space.guid]
        cls.cf_brokers = ServiceBroker.cf_api_get_list(core_space.guid)

        cls.step("Retrieve apps and services present on the Platform")
        cls.platform_apps = Application.api_get_list(core_space.guid)
        cls.platform_instances = ServiceInstance.api_get_list(core_space.guid)

    def test_all_required_apps_are_present_in_cf(self):
        self.step("Check that all expected apps are present in cf")
        cf_app_names = {a.name for a in self.cf_apps}
        missing_apps = self.expected_app_names - cf_app_names
        self.assertEqual(missing_apps, set(), "Apps missing in cf")

    def test_all_required_apps_are_running_in_cf(self):
        self.step("Check that all expected apps have running instances in cf")
        apps_not_running = {a.name for a in self.cf_apps
                            if a.name in self.expected_app_names - self.EXCLUDED_APP_NAMES and not a.is_running}
        self.assertEqual(apps_not_running, set(), "Apps with no running instances in cf")

    def test_all_required_apps_are_present_on_platform(self):
        self.step("Check that all expected apps are present on the Platform")
        app_names = {a.name for a in self.platform_apps}
        missing_apps = self.expected_app_names - app_names
        self.assertEqual(missing_apps, set(), "Apps missing on the Platform")

    def test_all_required_apps_are_running_on_platform(self):
        self.step("Check that all expected apps have running instances on the Platform")
        apps_not_running = {a.name for a in self.platform_apps
                            if a.name in self.expected_app_names - self.EXCLUDED_APP_NAMES and not a.is_running}
        self.assertEqual(apps_not_running, set(), "Apps with no running instances on the Platform")

    def test_apps_have_the_same_details_in_cf_and_on_platform(self):
        only_expected_platform_apps = {app for app in self.platform_apps if app.name in self.expected_app_names}
        for app in only_expected_platform_apps:
            with self.subTest(app=app.name):
                self.step("Check that details of app {} are the same in cf and on the Platform".format(app.name))
                cf_details = app.cf_api_get_summary()
                platform_details = app.api_get_summary()
                self.assertEqual(cf_details, platform_details, "Different details for {}".format(app.name))

    def test_all_required_service_instances_are_present_in_cf(self):
        self.step("Check that all expected services are present in cf")
        excluded_names = {s.name for s in self.cf_upsi + self.cf_apps}
        missing_services = self.expected_upsi_names - excluded_names
        self.assertEqual(missing_services, set(), "Services missing in cf")

    def test_all_required_service_instances_are_present_on_platform(self):
        self.step("Check that all expected services are present on the Platform")
        excluded_names = {s.name for s in self.platform_instances + self.platform_apps}
        missing_services = self.expected_upsi_names - excluded_names
        self.assertEqual(missing_services, set(), "Services missing on the Platform")

    def test_all_required_brokers_are_present_in_cf(self):
        self.step("Check that all expected service brokers are present in cf")
        cf_broker_names = {b.name for b in self.cf_brokers}
        missing_brokers = self.expected_broker_names - cf_broker_names
        self.assertEqual(missing_brokers, set(), "Brokers missing in cf")

    @long
    def test_spring_services_dont_expose_sensitive_endpoints(self):
        SENSITIVE_ENDPOINTS = ["actuator", "autoconfig", "beans", "configprops", "docs", "dump", "env", "flyway",
                               "info", "liquidbase", "logfile", "metrics", "mappings", "shutdown", "trace"]
        client = AppClient.get_admin_client()
        for url in [a.urls[0] for a in self.platform_apps
                    if a.name in self.expected_app_names - self.SENSITIVE_ENDPOINTS_EXCLUDED_APPS]:
            app_name = url.split(".")[0]
            try:
                client.request(method="GET", endpoint="health", app_name=app_name)
            except UnexpectedResponseError:
                logger.info("Not checking {} service".format(app_name))
                continue
            with self.subTest(app_name=app_name):
                self.step("Check that the sensitive endpoints are not enabled.")
                enabled_endpoints = []
                for endpoint in SENSITIVE_ENDPOINTS:
                    try:
                        client.request(method="GET", endpoint=endpoint, app_name=app_name)
                    except UnexpectedResponseError:
                        continue
                    else:
                        enabled_endpoints.append(endpoint)
                self.assertEqual(enabled_endpoints, [], "{} exposes {}".format(app_name, enabled_endpoints))
