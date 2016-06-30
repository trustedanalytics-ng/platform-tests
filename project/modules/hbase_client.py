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

import json

import requests

from .exceptions import UnexpectedResponseError
from .tap_logger import log_http_request, log_http_response
from .http_calls import cloud_foundry as cf


class HbaseClient(object):

    API_TABLES_ENDPOINT = "api/tables"
    HBASE_CLIENT_NAME = "Hbase Client"

    def __init__(self, app_hbase_reader):
        self.app = app_hbase_reader
        self.tables = []
        self.session = requests.Session()

    def get_namespace(self):
        reader_env = cf.cf_api_get_app_env(self.app.guid)
        return reader_env.get("system_env_json")\
            .get("VCAP_SERVICES")\
            .get("hbase")[0]\
            .get("credentials")\
            .get("hbase.namespace")

    def create_table(self, table_name, column_families=None):
        column_families = ["post"] if column_families is None else column_families
        self.request(
            method="POST",
            instance_url=self.app.urls[0],
            endpoint=self.API_TABLES_ENDPOINT,
            username=self.HBASE_CLIENT_NAME,
            body={'tableName': table_name, 'columnFamilies': column_families},
            message_on_error="Failed create hbase table")

    def get_tables(self):
        response = self.request(
            method="GET",
            instance_url=self.app.urls[0],
            endpoint=self.API_TABLES_ENDPOINT,
            username=self.HBASE_CLIENT_NAME,
            message_on_error="Failed get hbase tables")
        for table in response:
            self.tables.append(table["tableName"])
        return self.tables

    def get_table_row(self, table_name, row_key):
        response = self.request(
            method="GET",
            instance_url=self.app.urls[0],
            endpoint="{}/{}/row/{}".format(self.API_TABLES_ENDPOINT, table_name, row_key),
            username=self.HBASE_CLIENT_NAME,
            message_on_error="Failed get table row")
        return response

    def get_first_rows_from_table(self, table_name):
        table_rows = []
        response = self.request(
            method="GET",
            instance_url=self.app.urls[0],
            endpoint="{}/{}/{}".format(self.API_TABLES_ENDPOINT, table_name, "head"),
            username=self.HBASE_CLIENT_NAME,
            message_on_error="Failed get first rows from hbase table")
        for rows in response:
            table_rows.append(rows)
        return table_rows

    def request(self, method, instance_url, endpoint, username, body=None, data=None, params=None, files=None,
                message_on_error=""):
        request = requests.Request(
            method=method,
            url="http://{}/{}".format(instance_url, endpoint),
            data=data,
            params=params,
            json=body,
            files=files
        )
        request = self.session.prepare_request(request)
        log_http_request(request, username=username)
        response = self.session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(status=response.status_code, error_message=message_on_error)
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text
