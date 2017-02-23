#
# Copyright (c) 2016 - 2017 Intel Corporation
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
from tests.fixtures.assertions import assert_dict_values_set

logged_components = (TAP.user_management, TAP.auth_gateway, TAP.das, TAP.downloader, TAP.metadata_parser,
                     TAP.data_catalog, TAP.service_catalog, TAP.gearpump_broker,
                     TAP.hbase_broker, TAP.hdfs_broker, TAP.kafka_broker, TAP.smtp_broker, TAP.yarn_broker,
                     TAP.zookeeper_broker, TAP.zookeeper_wssb_broker, TAP.platform_tests)
pytestmark = [priority.high]

expected_metrics_keys = ["apps_running", "apps_down", "users_org", "service_usage", "memory_usage_org", "cpu_usage_org",
                         "private_datasets", "public_datasets"]


@pytest.mark.components(TAP.metrics_grafana)
def test_dashboard_metrics():
    """
    <b>Description:</b>
    Checks if platform returns following Dashboard Metrics: "apps_running", "apps_down", "users_org", "service_usage",
    "memory_usage_org", "cpu_usage_org", "private_datasets", "public_datasets".

    <b>Input data:</b>
    No input data.

    <b>Expected results:</b>
    Test passes when Grafana returns all expected metrics i.e. "apps_running", "apps_down", "users_org",
    "service_usage", "memory_usage_org", "cpu_usage_org", "private_datasets", "public_datasets".

    <b>Steps:</b>
    1. Get metrics from Grafana.
    2. Verify that Grafana returned following metrics: "apps_running", "apps_down", "users_org", "service_usage",
    "memory_usage_org", "cpu_usage_org", "private_datasets", "public_datasets".
    """
    step("Get metrics from Grafana")
    dashboard_metrics = Metrics.from_grafana()
    step("Check if all expected metrics returned")
    assert_dict_values_set(vars(dashboard_metrics), expected_metrics_keys)
