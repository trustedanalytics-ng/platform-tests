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

import pytest

from modules.constants import TapComponent as TAP, UserManagementHttpStatus
from modules.http_calls.platform import metrics_provider, router_metrics_provider
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import DataSet, User
from modules.tap_object_model.flows import summaries
from tests.fixtures.assertions import assert_raises_http_exception, assert_returns_http_success_with_retry

logged_components = (TAP.metrics_provider, TAP.router_metrics_provider)
pytestmark = [pytest.mark.components(TAP.metrics_provider, TAP.router_metrics_provider)]

expected_metrics_keys = ["appsDown", "appsRunning", "datasetCount", "domainsUsage", "domainsUsagePercent",
                         "latestEvents", "memoryUsage", "memoryUsageAbsolute", "privateDatasets", "publicDatasets",
                         "serviceUsage", "serviceUsagePercent", "totalUsers"]


class TestMetrics(object):
    org_apps = org_services = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def get_org_metrics(cls, core_org):
        step("Retrieve metrics for the core organization")
        core_org.api_get_metrics()
        cls.org_apps, cls.org_services = summaries.cf_api_get_org_summary(org_guid=core_org.guid)
        cls.org_guid = core_org.guid

    @staticmethod
    def stop_start_application(self, app_name, http_request, *args):
        step("Turn off the app, then check that it starts properly.")
        tested_app = next((x for x in self.org_apps if x.name == app_name), None)
        assert tested_app is not None, "The application does not exist"
        tested_app.ensure_started()
        tested_app.api_stop()
        tested_app.ensure_stopped()
        assert_raises_http_exception(UserManagementHttpStatus.CODE_NOT_FOUND, UserManagementHttpStatus.MSG_NOT_FOUND,
                                     http_request, *args)
        tested_app.api_start()
        tested_app.ensure_started()
        assert_returns_http_success_with_retry(http_request, *args)

    @priority.high
    def test_metrics_contains_all_keys(self, core_org):
        step("Check that metrics response contains all expected fields")
        keys = list(core_org.metrics.keys())
        assert keys.sort() == expected_metrics_keys.sort()

    @priority.low
    def test_service_count(self, core_org):
        step("Get services from cf and check that serviceUsage metrics is correct")
        assert core_org.metrics["serviceUsage"] == len(self.org_services)

    @priority.low
    def test_application_metrics(self, core_org):
        step("Get apps from cf and check that appsRunning and appsDown metrics are correct")
        cf_apps_up = []
        cf_apps_down = []
        for app in self.org_apps:
            if app.is_started:
                cf_apps_up.append(app.name)
            else:
                cf_apps_down.append(app.name)
        dashboard_apps_running = core_org.metrics["appsRunning"]
        dashboard_apps_down = core_org.metrics["appsDown"]
        metrics_are_equal = (len(cf_apps_up) == dashboard_apps_running and len(cf_apps_down) == dashboard_apps_down)
        error_msg = "\nApps running: {}, expected: {}\n({})\nApps down: {}, expected: {}\n({})".format(
            dashboard_apps_running, len(cf_apps_up), cf_apps_up,
            dashboard_apps_down, len(cf_apps_down), cf_apps_down)
        assert metrics_are_equal is True, error_msg

    @priority.low
    def test_user_count(self, core_org):
        step("Get org users from cf and check that totalUsers metrics is correct")
        cf_user_list = User.cf_api_get_list_in_organization(org_guid=core_org.guid)
        dashboard_total_users = core_org.metrics["totalUsers"]
        assert len(cf_user_list) == dashboard_total_users, "\nUsers: {}, expected: {}".format(
            dashboard_total_users, len(cf_user_list))

    @priority.low
    def test_data_metrics(self, core_org):
        step("Get datasets and check datasetCount, privateDatasets, publicDatasets metrics are correct")
        public_datasets = []
        private_datasets = []
        datasets = DataSet.api_get_list([core_org])
        for table in datasets:
            if table.is_public:
                public_datasets.append(table)
            else:
                private_datasets.append(table)
        dashboard_datasets_count = core_org.metrics['datasetCount']
        dashboard_private_datasets = core_org.metrics['privateDatasets']
        dashboard_public_datasets = core_org.metrics['publicDatasets']
        metrics_are_equal = (len(datasets) == dashboard_datasets_count and
                             len(private_datasets) == dashboard_private_datasets and
                             len(public_datasets) == dashboard_public_datasets)
        error_msg = "\nDatasets: {}, expected: {}\nPrivate: {}, expected: {}\nPublic: {}, expected: {}".format(
            dashboard_datasets_count, len(datasets),
            dashboard_private_datasets, len(private_datasets),
            dashboard_public_datasets, len(public_datasets))
        assert metrics_are_equal is True, error_msg

    @priority.low
    def test_router_metrics_provider(self):
        self.stop_start_application(self, TAP.router_metrics_provider,
                                    router_metrics_provider.api_get_router_metrics)

    @priority.low
    def test_metrics_provider(self, core_org):
        self.stop_start_application(self, TAP.metrics_provider, metrics_provider.api_get_org_metrics,
                                    core_org.guid)

