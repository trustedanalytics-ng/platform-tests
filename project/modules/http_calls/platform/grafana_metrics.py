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

import time

from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.configuration_provider.grafana import GrafanaConfigurationProvider
from ...http_client.http_client_factory import HttpClientFactory

def api_get_metric(client=None, panel_id=None, metrics_level=None):
    """GET /api/datasources/proxy/1/api/v1/query_range"""
    client = client or HttpClientFactory.get(GrafanaConfigurationProvider.get())
    timestamp = int(time.time())
    start = timestamp
    end = timestamp
    step = "2"
    headers_referer = "{}/dashboard-solo/db/organization-dashboard?panelId={}&from=now&to=now".format(client.url, panel_id)
    dashboard_queries = {
        "3": "tap_usermanagement_counts{component='users'}",
        "5": "sum(container_memory_usage_bytes{image!=''})",
        "6": "sum(sum by (kubernetes_pod_name)  (rate(container_cpu_usage_seconds_total{image!=''}[2m]))) / sum(machine_cpu_cores) "
    }
    if metrics_level == "platform":
        step = "60"
        headers_referer = "{}/dashboard-solo/db/platform-dashboard?panelId={}&from=now-1h&to=now".format(client.url, panel_id)
        dashboard_queries = {
            "1": "tap_catalog_counts{component='applications'}",
            "2": "tap_catalog_counts{component='services'}",
            "3": "tap_catalog_counts{component='serviceInstances'}",
            "4": "1",
            "5": "tap_usermanagement_counts{component='users'}",
            "7": "sum(container_memory_usage_bytes{image!=''})",
            "8": "sum(sum by (kubernetes_pod_name)  (rate(container_cpu_usage_seconds_total{image!=''}[2m]))) / sum(machine_cpu_cores) "
        }
    query = dashboard_queries.get(panel_id, "42")
    return client.request(
        method=HttpMethod.GET,
        path="api/datasources/proxy/1/api/v1/query_range",
        headers={"Referer": headers_referer},
        params={"query": query, "start": start, "end": end, "step": step},
        msg="GRAFANA: get metrics"
    )
