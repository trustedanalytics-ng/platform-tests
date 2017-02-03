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

from config import console_url
from modules.constants import HttpStatus, TapComponent as TAP
from modules.tap_logger import step
from modules.tap_object_model import Metrics, User
from tests.fixtures import assertions
from modules.http_client.client_auth.http_method import HttpMethod

logged_components = (TAP.platform_operations, )
pytestmark = [pytest.mark.components(TAP.platform_operations)]


@pytest.mark.usefixtures("open_tunnel")
class TestOperationsMetrics:
    """
    Operations Metrics test can be unstable when run parallel
    with other tests since it check for resources count
    """
    MAX_CHECK = 3
    MARGIN_ERROR = 10  # because grafana use moving-average for last 1-2m

    def _get_metrics(self, org_guid):
        """Return metrics from operations platform dashboard and reference metrics"""
        platform = Metrics.from_grafana(metrics_level="platform")
        reference_data = Metrics.from_reference(org_guid)
        return platform, reference_data

    def values_to_compare(self, checked_metrics_attribute, org_guid):
        """
        this function is created to help with test instability when running in parallel
        with other tests. It asserts if values are correct, if not it gathers new data.
        This function should run max=MAX_CHECK times during this TestCase execution
        :param checked_metrics_attribute: current metrics to check
        :return:
        """
        for _ in range(self.MAX_CHECK):
            operations_metrics, ref_metrics = self._get_metrics(org_guid)
            operations_metrics_value = getattr(operations_metrics, checked_metrics_attribute)
            ref_metrics_value = getattr(ref_metrics, checked_metrics_attribute)
            if operations_metrics_value == ref_metrics_value:
                return operations_metrics_value, ref_metrics_value
        return operations_metrics_value, ref_metrics_value

    @pytest.mark.parametrize("metrics_attribute", ("apps", "services", "service_instances", "orgs", "users_platform"))
    @pytest.mark.bugs("DPNG-14031 Number of User accounts in Dashboard changes to actual amount but after a while")
    def test_operations_metrics(self, metrics_attribute, test_org):
        """
        <b>Description:</b>
        Checks if metrics for "apps", "services", "service_instances", "orgs", "users_platform" show correct values on
        Platform Dashboard Summary page.

        <b>Input data:</b>
        1. Metric names.

        <b>Expected results:</b>
        Test passes when metric values or "apps", "services", "service_instances", "orgs", "users_platform" on Platform
        Dashboard Summary page equal values retrieved from Grafana.

        <b>Steps:</b>
        1. Retrieve reference and platform metrics.
        2. Verify that reference values equal platform metrics.
        """
        step("Testing if reference values equals platform data. Data to check: {}".format(metrics_attribute))
        operation_metrics, ref_metrics = self.values_to_compare(metrics_attribute, test_org.guid)
        assert operation_metrics == ref_metrics, "Grafana metrics {} are not equal to references metrics {}" \
                                                 "".format(operation_metrics, ref_metrics)

    @pytest.mark.parametrize("metrics_attribute", ("memory_usage_platform", "cpu_usage_platform"))
    def test_operations_metrics_cpu_and_memory(self, metrics_attribute, test_org):
        """
        <b>Description:</b>
        Checks if metrics for "memory_usage_platform", "cpu_usage_platform" show correct values on Platform Dashboard
        Summary page.

        <b>Input data:</b>
        1. Metric names.

        <b>Expected results:</b>
        Test passes when metric values for "memory_usage_platform", "cpu_usage_platform" on Platform Dashboard Summary
        page equal values retrieved from Grafana.

        <b>Steps:</b>
        1. Retrieve reference and platform metrics.
        2. Verify that reference values equal platform metrics with error margin.
        """
        step("Testing if reference values equals platform data. Data to check: {}".format(metrics_attribute))
        operation_metrics, ref_metrics = self.values_to_compare(metrics_attribute, test_org.guid)
        assert abs(operation_metrics - ref_metrics) < self.MARGIN_ERROR, \
            "Grafana metrics {} are not equals to references metrics {}".format(operation_metrics, ref_metrics)
