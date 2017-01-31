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

from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.http_client_configuration import HttpClientConfiguration
from modules.http_client.http_client_factory import HttpClientFactory
from modules.http_client.http_client_type import HttpClientType


def get_databases(app_url):
    """GET listDatabases"""
    configuration = HttpClientConfiguration(client_type=HttpClientType.BROKER, url=app_url)
    return HttpClientFactory.get(configuration).request(
        method=HttpMethod.GET,
        path="listDatabases",
        msg="OrientDB-dashboard: get list of databases"
    )


def get_database(database_name, password, app_url):
    """GET database/{database_name}"""
    configuration = HttpClientConfiguration(client_type=HttpClientType.BROKER, username="root",
                                            password=password, url=app_url)
    return HttpClientFactory.get(configuration).request(
        method=HttpMethod.GET,
        path="database/{database_name}",
        path_params={'database_name': database_name},
        msg="OrientDB-dashboard: get database"
    )


def execute_command(database_name, command, password, app_url):
    """GET command/{database_name}/sql/{command}/20"""
    configuration = HttpClientConfiguration(client_type=HttpClientType.BROKER, username="root",
                                            password=password, url=app_url)
    return HttpClientFactory.get(configuration).request(
        method=HttpMethod.GET,
        path="command/{database_name}/sql/{command}/20",
 path_params={'database_name': database_name, 'command': command},
        msg="OrientDB-dashboard: execute command"
    )
