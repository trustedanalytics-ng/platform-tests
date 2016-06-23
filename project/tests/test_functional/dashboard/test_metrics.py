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

from modules.constants import TapComponent as TAP
from modules.runner.tap_test_case import TapTestCase
from modules.markers import components, priority
from modules.tap_object_model import DataSet, User
from modules.tap_object_model.flows import summaries
from tests.fixtures.test_data import TestData


logged_components = (TAP.metrics_provider,)
pytestmark = [components.metrics_provider]


expected_metrics_keys = ["appsDown", "appsRunning", "datasetCount", "domainsUsage", "domainsUsagePercent",
                         "latestEvents", "memoryUsage", "memoryUsageAbsolute", "privateDatasets", "publicDatasets",
                         "serviceUsage", "serviceUsagePercent", "totalUsers"]


class Metrics(TapTestCase):
    org_apps = org_services = None

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def get_org_metrics(cls, core_org):
        cls.step("Retrieve metrics for the core organization")
        core_org.api_get_metrics()
        cls.org_apps, cls.org_services = summaries.cf_api_get_org_summary(org_guid=core_org.guid)

    @priority.high
    def test_metrics_contains_all_keys(self):
        self.step("Check that metrics response contains all expected fields")
        keys = list(TestData.core_org.metrics.keys())
        self.assertUnorderedListEqual(keys, expected_metrics_keys)

    @priority.low
    def test_service_count(self):
        self.step("Get services from cf and check that serviceUsage metrics is correct")
        self.assertEqual(TestData.core_org.metrics["serviceUsage"], len(self.org_services))

    @priority.low
    def test_application_metrics(self):
        self.step("Get apps from cf and check that appsRunning and appsDown metrics are correct")
        cf_apps_up = []
        cf_apps_down = []
        for app in self.org_apps:
            if app.is_started:
                cf_apps_up.append(app.name)
            else:
                cf_apps_down.append(app.name)
        dashboard_apps_running = TestData.core_org.metrics["appsRunning"]
        dashboard_apps_down = TestData.core_org.metrics["appsDown"]
        metrics_are_equal = (len(cf_apps_up) == dashboard_apps_running and len(cf_apps_down) == dashboard_apps_down)
        self.assertTrue(metrics_are_equal,
                        "\nApps running: {} - expected: {}\n({})"
                        "\nApps down: {} - expected: {}\n({})".format(dashboard_apps_running, len(cf_apps_up),
                                                                      cf_apps_up, dashboard_apps_down,
                                                                      len(cf_apps_down), cf_apps_down))

    @priority.low
    def test_user_count(self):
        self.step("Get org users from cf and check that totalUsers metrics is correct")
        cf_user_list = User.cf_api_get_list_in_organization(org_guid=TestData.core_org.guid)
        dashboard_total_users = TestData.core_org.metrics["totalUsers"]
        self.assertEqual(len(cf_user_list), dashboard_total_users,
                         "\nUsers: {} - expected: {}".format(dashboard_total_users, len(cf_user_list)))

    @priority.low
    def test_data_metrics(self):
        self.step("Get datasets and check datasetCount, privateDatasets, publicDatasets metrics are correct")
        public_datasets = []
        private_datasets = []
        datasets = DataSet.api_get_list([TestData.core_org])
        for table in datasets:
            if table.is_public:
                public_datasets.append(table)
            else:
                private_datasets.append(table)
        dashboard_datasets_count = TestData.core_org.metrics['datasetCount']
        dashboard_private_datasets = TestData.core_org.metrics['privateDatasets']
        dashboard_public_datasets = TestData.core_org.metrics['publicDatasets']
        metrics_are_equal = (len(datasets) == dashboard_datasets_count and
                             len(private_datasets) == dashboard_private_datasets and
                             len(public_datasets) == dashboard_public_datasets)
        self.assertTrue(metrics_are_equal,
                        "\nDatasets count: {} - expected: {}\nPrivate datasets: {} - expected: {}"
                        "\nPublic datasets: {} - expected: {}".format(dashboard_datasets_count, len(datasets),
                                                                      dashboard_private_datasets, len(private_datasets),
                                                                      dashboard_public_datasets, len(public_datasets)))
