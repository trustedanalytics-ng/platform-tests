#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import requests

from enum import Enum

from .exceptions import UnexpectedResponseError
from .tap_logger import log_http_response, log_http_request


class WebhdfsOperation(Enum):
    get_content_summary = "GETCONTENTSUMMARY"
    open = "OPEN"
    get_file_status = "GETFILESTATUS"
    list_status = "LISTSTATUS"


class WebhdfsClient(object):

    DEFAULT_PORT = 50070
    DEFAULT_USER = "cf"

    def __init__(self, host, port=DEFAULT_PORT, user_name=DEFAULT_USER):
        self.__host = host
        self.__port = port
        self.__user_name = user_name
        self.__session = requests.Session()

    @property
    def __url(self):
        return "http://{}:{}/webhdfs/v1/".format(self.__host, self.__port)

    def __get_params(self, operation):
        return {"op": operation, "user.name": self.__user_name}

    def __send_request(self, method, body=None, params=None, hdfs_path=""):
        url = self.__url() + hdfs_path
        request = requests.Request(
            method=method,
            url=url,
            params=params,
            json=body
        )
        request = self.__session.prepare_request(request)
        log_http_request(request, username=params["user_name"])
        response = self.__session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(status=response.status_code, error_message=response.text)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text

    def get_content_summary(self, hdfs_path):
        params = self.__get_params(WebhdfsOperation.get_content_summary)
        return self.__send_request("GET", params=params, hdfs_path=hdfs_path)

    def open_and_read(self, hdfs_path):
        params = self.__get_params(WebhdfsOperation.open)
        return self.__send_request("GET", params=params, hdfs_path=hdfs_path)

    def get_file_status(self, hdfs_path):
        params = self.__get_params(WebhdfsOperation.get_file_status)
        return self.__send_request("GET", params=params, hdfs_path=hdfs_path)

    def list_directory(self, hdfs_path):
        params = self.__get_params(WebhdfsOperation.list_status)
        return self.__send_request("GET", params=params, hdfs_path=hdfs_path)
