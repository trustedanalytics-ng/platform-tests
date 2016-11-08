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

from modules.constants import HttpStatus, TapComponent as TAP
from modules.tap_logger import step
from modules.tap_object_model import Metrics
from tests.fixtures import assertions


logged_components = (TAP.platform_operations, )
pytestmark = [pytest.mark.components(TAP.platform_operations)]


class TestNonAdminOperationsMetrics:

    @pytest.mark.skip("DPNG-5904: Operations/Platform - non-logged-in user get session expired",
                      "DPNG-10769 [TAP-NG] Metrics - E2E tests")
    def test_non_admin_cannot_access_platform_operations(self, test_org_manager_client):
        step("Checking if non-admin user cannot retrieve data")
        metrics = Metrics()
        ref_metrics = metrics.from_reference()
        grafana_metrics = metrics.from_grafana()
        assertions.assert_raises_http_exception(HttpStatus.CODE_UNAUTHORIZED, HttpStatus.MSG_UNAUTHORIZED,
                                                ref_metrics, test_org_manager_client)
        assertions.assert_raises_http_exception(HttpStatus.CODE_UNAUTHORIZED, HttpStatus.MSG_UNAUTHORIZED,
                                                grafana_metrics, test_org_manager_client)


@pytest.mark.bugs("DPNG-11096 Service Metrics - Catalog instrumentation")
@pytest.mark.usefixtures("open_tunnel")
class TestOperationsMetrics:
    """
    Operations Metrics test can be unstable when run parallel
    with other tests since it check for resources count
    """
    MAX_CHECK = 3
    MARGIN_ERROR = 10  # because grafana use moving-average for last 1-2m

    def _get_metrics(self):
        """Return metrics from operations platform dashboard and reference metrics"""
        platform = Metrics.from_grafana(metrics_level="platform")
        reference_data = Metrics.from_reference()
        return platform, reference_data

    def values_to_compare(self, checked_metrics_attribute):
        """
        this function is created to help with test instability when running in parallel
        with other tests. It asserts if values are correct, if not it gathers new data.
        This function should run max=MAX_CHECK times during this TestCase execution
        :param checked_metrics_attribute: current metrics to check
        :return:
        """
        for _ in range(self.MAX_CHECK):
            operations_metrics, ref_metrics = self._get_metrics()
            operations_metrics_value = getattr(operations_metrics, checked_metrics_attribute)
            ref_metrics_value = getattr(ref_metrics, checked_metrics_attribute)
            if operations_metrics_value == ref_metrics_value:
                return operations_metrics_value, ref_metrics_value
        return operations_metrics_value, ref_metrics_value

    @pytest.mark.parametrize("metrics_attribute", ("apps", "services", "service_instances", "orgs", "users_platform"))
    def test_operations_metrics(self, metrics_attribute):
        step("Testing if reference values equals platform data. Data to check: {}".format(metrics_attribute))
        operation_metrics, ref_metrics = self.values_to_compare(metrics_attribute)
        assert operation_metrics == ref_metrics, "Grafana metrics {} are not equals to references metrics {}" \
                                                 "".format(operation_metrics, ref_metrics)

    @pytest.mark.parametrize("metrics_attribute", ("memory_usage_platform", "cpu_usage_platform"))
    def test_operations_metrics_cpu_and_memory(self, metrics_attribute):
        step("Testing if reference values equals platform data. Data to check: {}".format(metrics_attribute))
        operation_metrics, ref_metrics = self.values_to_compare(metrics_attribute)
        assert abs(operation_metrics - ref_metrics) < self.MARGIN_ERROR, \
            "Grafana metrics {} are not equals to references metrics {}".format(operation_metrics, ref_metrics)
