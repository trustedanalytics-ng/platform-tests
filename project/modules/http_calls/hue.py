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

import functools

import config
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.configuration_provider.console import ConsoleConfigurationProvider
from modules.http_client.configuration_provider.service_tool import ServiceToolConfigurationProvider
from modules.http_client.http_client_factory import HttpClientFactory

console_client = HttpClientFactory.get(ConsoleConfigurationProvider.get())
client = HttpClientFactory.get(ServiceToolConfigurationProvider.get(url=config.hue_url))
client.session = console_client.session


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for _ in range(5):
            response = func(*args, **kwargs)
            if "login required" in response:
                client.request(method=HttpMethod.GET, path="", msg="login")
            else:
                return response
        raise AssertionError("Could not login to hue api")
    return wrapper


@login_required
def get_databases():
    """GET metastore/databases"""
    return client.request(
        method=HttpMethod.GET,
        path="metastore/databases",
        params={"format": "json"},
        msg="HUE: get list of databases"
    )


@login_required
def get_tables(database_name):
    """GET metastore/tables/{database_name}"""
    return client.request(
        method=HttpMethod.GET,
        path="metastore/tables/{}".format(database_name),
        msg="HUE: get tables"
    )


@login_required
def get_table(database_name, table_name):
    """GET metastore/table/{database_name}/{table_name}"""
    return client.request(
        method=HttpMethod.GET,
        path="metastore/table/{}/{}".format(database_name, table_name),
        msg="HUE: get table"
    )


@login_required
def get_file_browser():
    """GET filebrowser"""
    return client.request(
        method=HttpMethod.GET,
        path="filebrowser",
        params={"format": "json"},
        msg="HUE: file browser"
    )


@login_required
def get_job_browser():
    """GET jobbrowser"""
    return client.request(
        method=HttpMethod.GET,
        path="jobbrowser",
        params={"format": "json"},
        msg="HUE: get job browser"
    )