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

import os

from enum import Enum

from modules.constants.http_status import HttpStatus
from configuration.config import CONFIG
from modules.http_client.http_client_factory import HttpClientFactory, HttpClientConfiguration, HttpClientType
from modules.http_client.client_auth.webhdfs_session import WebhdfsSession
from modules.http_client.client_auth.http_method import HttpMethod
from modules.http_client.http_client import HttpClient


class WebhdfsOperation(Enum):
    get_content_summary = "GETCONTENTSUMMARY"
    open = "OPEN"
    get_file_status = "GETFILESTATUS"
    list_status = "LISTSTATUS"


class WebhdfsTools(object):

    DEFAULT_PORT = 50070
    TEST_PORT = 1234
    TEST_HOST = "localhost"
    DEFAULT_USER = "hdfs"
    VIA_HOST_USERNAME = "ubuntu"
    PATH_TO_KEY = os.path.expanduser(CONFIG["cdh_key_path"])

    @staticmethod
    def get_params(operation):
        return {"op": operation, "user.name": WebhdfsTools.DEFAULT_USER}

    @staticmethod
    def get_content_summary(client: HttpClient, path):
        params = WebhdfsTools.get_params(WebhdfsOperation.get_content_summary.value)
        return client.request(method=HttpMethod.GET, path=path, params=params)

    @staticmethod
    def open_and_read(client: HttpClient, path):
        params = WebhdfsTools.get_params(WebhdfsOperation.open.value)
        response = client.request(method=HttpMethod.GET, params=params, path=path)
        if response.status_code == HttpStatus.CODE_TEMPORARY_REDIRECT:
            return WebhdfsSession.redirection_handler(
                WebhdfsTools.create_client, WebhdfsTools.TEST_PORT, WebhdfsTools.VIA_HOST_USERNAME,
                WebhdfsTools.PATH_TO_KEY, WebhdfsTools.get_via_hostname, WebhdfsTools.TEST_HOST, method=HttpMethod.GET,
                params=params, redirection_location=response.headers._store["location"][1], hdfs_path=path)
        return response

    @staticmethod
    def get_file_status(client: HttpClient, path):
        params = WebhdfsTools.get_params(WebhdfsOperation.get_file_status.value)
        return client.request(method=HttpMethod.GET, params=params, path=path)

    @staticmethod
    def list_directory(client: HttpClient, path):
        params = WebhdfsTools.get_params(WebhdfsOperation.list_status.value)
        return client.request(method=HttpMethod.GET, params=params, path=path)

    @staticmethod
    def get_via_hostname():
        return "jump.{}".format(CONFIG["domain"])

    @staticmethod
    def create_client(host=" ", port=DEFAULT_PORT):
        url = "{}:{}".format(host, str(port))
        client_configuration = HttpClientConfiguration(HttpClientType.WEBHDFS, url=url, username=host,
                                                       password=str(port))
        client = HttpClientFactory.get(client_configuration)
        if "webhdfs" not in client.url:
            client.url = "http://{}/webhdfs/v1/".format(client.url)
        return client
