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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import Metrics
from modules.tap_logger import log_fixture
from tests.fixtures.assertions import assert_dict_values_set


logged_components = (TAP.metrics_grafana, TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.metrics_grafana)]

expected_metrics_keys = ["apps_running", "apps_down", "users_org", "service_usage", "memory_usage_org", "cpu_usage_org",
                         "datasets"]


@pytest.mark.usefixtures("open_tunnel")
class TestMetrics(object):

    MARGIN_ERROR = 10  # because grafana use moving-average for last 1-2m

    @pytest.fixture(scope="class")
    def org_metrics(self, test_org):
        log_fixture("Retrieve metrics for the organization")
        reference_metrics = Metrics.from_reference(test_org.guid)
        org_metrics = Metrics.from_grafana()
        return reference_metrics, org_metrics

    @priority.high
    def test_metrics_contains_all_values(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show values of expected metrics: "apps_running", "apps_down", "users_org",
        "service_usage", "memory_usage_org", "cpu_usage_org", "datasets".

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when all metrics on Dashboard show values in correct formats.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metrics response contains all expected values: "apps_running", "apps_down", "users_org",
        "service_usage", "memory_usage_org", "cpu_usage_org", "datasets".
        """
        step("Check that metrics response contains all expected values")
        ref_metrics, grafana_metrics = org_metrics
        assert_dict_values_set(vars(grafana_metrics), expected_metrics_keys)

    @priority.low
    def test_apps_running(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show correct value of running applications.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when metric of running applications on Dashboard shows correct value.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metric of running applications on Dashboard shows correct value.
        """
        step("Get running apps and check that apps down metrics is correct")
        ref_metrics, grafana_metrics = org_metrics
        apps = ref_metrics.apps_running
        dashboard_running_apps = grafana_metrics.apps_running
        assert apps == dashboard_running_apps, "\nRunning apps in dashboard received from grafana: {}, " \
                                               "expected from reference: {}".format(dashboard_running_apps, apps)

    @priority.low
    def test_apps_down(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show correct value of stopped applications.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when metric of stopped applications on Dashboard shows correct value.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metric of stopped applications on Dashboard shows correct value.
        """
        step("Get down apps and check that apps down metrics is correct")
        ref_metrics, grafana_metrics = org_metrics
        apps = ref_metrics.apps_down
        dashboard_apps_down = grafana_metrics.apps_down
        assert apps == dashboard_apps_down, "\nDown apps in dashboard received from grafana: {}, expected from " \
                                            "reference: {}".format(dashboard_apps_down, apps)

    @priority.low
    def test_user_count(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show correct number of user accounts.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when metric of user accounts on Dashboard shows correct value.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metric of user accounts on Dashboard shows correct value.
        """
        step("Get org users and check that total users metrics is correct")
        ref_metrics, grafana_metrics = org_metrics
        user_list = ref_metrics.users_org
        dashboard_total_users = grafana_metrics.users_org
        assert user_list == dashboard_total_users, "\nUsers in dashboard received from grafana: {}, expected from" \
                                                   "reference: {}".format(dashboard_total_users, user_list)

    @priority.high
    def test_service_usage(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show correct number of running services.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when metric of running services on Dashboard shows correct value.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metric of running services on Dashboard shows correct value.
        """
        step("Get services and check that service usage metrics is correct")
        ref_metrics, grafana_metrics = org_metrics
        services = ref_metrics.service_usage
        dashboard_service_usage = grafana_metrics.service_usage
        assert services == dashboard_service_usage, "\nService usage in dashboard received from grafana: {}, expected" \
                                                    "from reference: {}".format(dashboard_service_usage, services)

    @priority.low
    def test_cpu_usage(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show correct value of CPU usage.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when metric of CPU usage on Dashboard shows correct value within error margin.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metric of CPU usage on Dashboard shows correct value within error margin.
        """
        step("Get CPU and check that cpu usage metrics is correct")
        ref_metrics, grafana_metrics = org_metrics
        cpu_metrics_ref = ref_metrics.cpu_usage_org
        cpu_metrics_dashboard = grafana_metrics.cpu_usage_org
        assert abs(cpu_metrics_ref - cpu_metrics_dashboard) < self.MARGIN_ERROR, \
            "\nCPU in dashboard received from grafana: {}, expected from reference: " \
            "{}".format(cpu_metrics_dashboard, cpu_metrics_ref)

    @priority.low
    def test_memory_usage(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show correct value of memory usage.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when metric of memory usage on Dashboard shows correct value within error margin.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metric of memory usage on Dashboard shows correct value within error margin.
        """
        step("Get memory and check that memory usage metrics is correct")
        ref_metrics, grafana_metrics = org_metrics
        memory_metrics_ref = ref_metrics.memory_usage_org
        memory_metrics_dashboard = grafana_metrics.memory_usage_org
        assert abs(memory_metrics_ref == memory_metrics_dashboard) < self.MARGIN_ERROR, \
            "\nMemory in dashboard received from grafana: {}, expected from reference: " \
            "{}".format(memory_metrics_dashboard, memory_metrics_ref)

    @priority.low
    def test_data_metrics(self, org_metrics):
        """
        <b>Description:</b>
        Checks if metrics on Dashboard show correct number of datasets.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes when metric of datasets on Dashboard shows correct value.

        <b>Steps:</b>
        1. Gather metrics from grafana and reference sources.
        2. Check that metric of datasets on Dashboard shows correct value.
        """
        step("Get datasets and check datasets metrics are correct")
        ref_metrics, grafana_metrics = org_metrics
        datasets_list_length = len(ref_metrics.datasets)
        dashboard_datasets = grafana_metrics.datasets
        assert datasets_list_length == dashboard_datasets
