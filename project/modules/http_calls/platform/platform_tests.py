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
import config

from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider
from ...http_client.http_client_factory import HttpClientFactory


def api_get_test_runs(client=None):
    """GET /platform_tests/tests"""
    client = client or HttpClientFactory.get(
        ConsoleConfigurationProvider.get(url=config.console_url_for_platform_tests_app)
    )
    return client.request(
        method=HttpMethod.GET,
        path="platform_tests/tests",
        msg="PLATFORM: get list of test runs"
    )


def api_get_test_run(run_id, client=None):
    """GET /platform_tests/tests/{suite_id}/results"""
    client = client or HttpClientFactory.get(
        ConsoleConfigurationProvider.get(url=config.console_url_for_platform_tests_app)
    )
    return client.request(
        method=HttpMethod.GET,
        path="platform_tests/tests/{run_id}/results",
        path_params={'run_id': run_id},
        msg="PLATFORM: get test run"
    )


def api_create_test_run(username, password, client=None):
    """POST /platform_tests/tests"""
    body = {
        "username": username,
        "password": password
    }
    client = client or HttpClientFactory.get(
        ConsoleConfigurationProvider.get(url=config.console_url_for_platform_tests_app)
    )
    return client.request(
        method=HttpMethod.POST,
        path="platform_tests/tests",
        body=body,
        msg="PLATFORM: create test run"
    )


def api_get_test_suites(client=None):
    """GET /platform_tests/tests/suites"""
    client = client or HttpClientFactory.get(
        ConsoleConfigurationProvider.get(url=config.console_url_for_platform_tests_app)
    )
    return client.request(
        method=HttpMethod.GET,
        path="platform_tests/tests/suites",
        msg="PLATFORM: get test suites"
    )
