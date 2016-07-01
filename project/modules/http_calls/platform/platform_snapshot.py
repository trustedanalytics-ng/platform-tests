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

from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.http_client_factory import HttpClientFactory
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider


def api_get_version(client=None):
    """GET /rest/v1/versions"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="/rest/v1/versions",
        msg="PLATFORM: get versions"
    )


def api_get_snapshots(client=None):
    """GET /rest/v1/snapshots"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="/rest/v1/snapshots",
        msg="PLATFORM: get snapshots"
    )


def api_trigger_snapshots(client=None):
    """GET /rest/v1/snapshots/trigger"""
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.GET,
        path="/rest/v1/snapshots/trigger",
        msg="PLATFORM: trigger snapshots"
    )
