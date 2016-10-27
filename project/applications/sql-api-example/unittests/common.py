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
import logging
import sys

import requests


INVALID_LABELS = ["", " ", "a b", ";", "a'); DROP TABLE users;--", "x"*64]
INVALID_TYPES = ["", " ", ";", "ab", "a'); DROP TABLE users;--", "x"*64]


logger = logging.getLogger("postgres app unittests")
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class HTTPResponseError(AssertionError):

    def __init__(self, code, message, description):
        super(HTTPResponseError, self).__init__()
        self.code = code
        self.message = message
        self.description = description


class ApiObject(object):
    SESSION = requests.session()
    APP_URL = "http://0.0.0.0:5000"

    @classmethod
    def handle_request(cls, request):
        request.url = cls.APP_URL + request.url
        request.headers = {"Accept": "application/json"}
        msg = ["------------ Request ------------",
               "{} {}".format(request.method, request.url),
               "Headers: {}".format(request.headers),
               "Body: {}".format(request.json),
               "---------------------------------"]
        logger.info("\n".join(msg))
        request = cls.SESSION.prepare_request(request)
        response = cls.SESSION.send(request)
        msg = ["------------ Response ------------",
               "Status code: {}".format(response.status_code),
               "Headers: {}".format(response.headers),
               "Body: {}".format(response.text),
               "----------------------------------"]
        logger.info("\n".join(msg))
        if not response.ok:
            response = json.loads(response.text)
            raise HTTPResponseError(
                code=response["status_code"],
                message=response["message"],
                description=response["description"]
            )
        try:
            return json.loads(response.text)
        except ValueError:
            return response.text


# class TestColumn(object):
#
#     def __init__(self, table_name, column_name, data_type, is_nullable=True, max_len=None):
#         self.table_name = table_name
#         self.name = column_name
#         self.data_type = data_type
#         self.is_nullable = is_nullable
#         self.max_len = max_len
#
#     def __eq__(self, other):
#         return self.table_name == other.table_name and self.name == other.name
#
#     def __hash__(self):
#         return hash((self.table_name, self.name))
#
#     @classmethod
#     def id_column(cls, table_name):
#         return cls(table_name=table_name, column_name="id", data_type="integer", is_nullable=False)
#
#     @classmethod
#     def from_json(cls, table_name, json_obj):
#         return cls(table_name=table_name, column_name=json_obj["name"], data_type=json_obj.get("type"),
#                    is_nullable=json_obj.get("is_nullable", True), max_len=json_obj.get("max_len", None))
#
#
# class TestTable(ApiObject):
#
#     TEST_TABLES = []
#
#     def __init__(self, name):
#         super(TestTable, self).__init__()
#         self.name = name
#
#     def __eq__(self, other):
#         return self.name == other.name
#
#     def __hash__(self):
#         return hash(self.name)
#
#     @classmethod
#     def create(cls, name, columns_json=None):
#         body = {"table_name": name}
#         if columns_json is not None:
#             body["columns"] = columns_json
#         request = requests.Request(method="POST", url="/tables", json=body)
#         response = cls.handle_request(request)
#         table = cls(name=response["table_name"])
#         cls.TEST_TABLES.append(table)
#         return table
#
#     @classmethod
#     def get_list(cls):
#         request = requests.Request(method="GET", url="/tables")
#         response = cls.handle_request(request)
#         return [cls(item["table_name"]) for item in response["/tables"]]
#
#     def get_columns(self):
#         request = requests.Request(method="GET", url="/tables/{}/columns".format(self.name))
#         response = self.handle_request(request)
#         return [TestColumn.from_json(self.name, item) for item in response["columns"]]
#
#     def delete(self):
#         request = requests.Request(method="DELETE", url="/tables/{}".format(self.name))
#         return self.handle_request(request)
#
#     @classmethod
#     def delete_test_tables(cls):
#         while len(cls.TEST_TABLES) > 0:
#             table = cls.TEST_TABLES.pop()
#             table.delete()
#
#
# class TestRow(ApiObject):
#
#     def __init__(self, table_name, row_id):
#         super(TestRow, self).__init__()
#         self.id = row_id
#         self.table_name = table_name
#
#     @classmethod
#     def create(cls, table_name, body):
#         request = requests.Request(method="POST", url="/tables/{}/rows".format(table_name), json=body)
#         return cls.handle_request(request)
#
#     @classmethod
#     def get(cls, table_name, row_id):
#         request = requests.Request(method="GET", url="/tables/{}/rows/{}".format(table_name, row_id))
#         return cls.handle_request(request)
#
#     @classmethod
#     def get_list(cls, table_name):
#         request = requests.Request(method="GET", url="/tables/{}/rows".format(table_name))
#         return cls.handle_request(request)
#
#     def update(self, body):
#         request = requests.Request(method="PUT", url="/tables/{}/rows/{}".format(self.table_name, self.id), json=body)
#         return self.handle_request(request)
#
#     def delete(self):
#         request = requests.Request(method="DELETE", url="/tables/{}/rows/{}".format(self.table_name, self.id))
#         return self.handle_request(request)



class PsqlColumn(ApiObject):

    COMPARABLE_ATTRS = ["name", "data_type", "is_nullable", "max_len"]

    def __init__(self, column_name, data_type, is_nullable, max_len):
        self.name = column_name
        self.data_type = data_type
        self.is_nullable = is_nullable or False
        self.max_len = max_len

    def __eq__(self, other):
        return all([getattr(self, a) == getattr(other, a) for a in self.COMPARABLE_ATTRS])

    def __hash__(self):
        return hash(*self.COMPARABLE_ATTRS)

    def __repr__(self):
        return "{} (name={}, data_type={}, is_nullable={}, max_len={})".format(self.__class__.__name__, self.name,
                                                                               self.data_type, self.is_nullable,
                                                                               self.max_len)

    @classmethod
    def from_json_definition(cls, column_json):
        return cls(column_json["name"], column_json["type"], column_json.get("is_nullable", True), column_json.get("max_len"))


class PsqlTable(ApiObject):

    TEST_TABLES = []

    def __init__(self, table_name):
        self.name = table_name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    @classmethod
    def post(cls, table_name, column_json):
        request = requests.Request(method="POST", url="/tables", json={"table_name": table_name, "columns": column_json})
        cls.handle_request(request)
        table = cls(table_name)
        cls.TEST_TABLES.append(table)
        return table

    @classmethod
    def get_list(cls):
        request = requests.Request(method="GET", url="/tables")
        response = cls.handle_request(request)
        tables = []
        for item in response["/tables"]:
            tables.append(cls(item["table_name"]))
        return tables

    def delete(self):
        request = requests.Request(method="DELETE", url="/tables/{}".format(self.name))
        self.handle_request(request)
        self.TEST_TABLES.remove(self)

    def get_columns(self):
        request = requests.Request(method="GET", url="/tables/{}/columns".format(self.name))
        response = self.handle_request(request)
        columns = []
        for item in response["columns"]:
            columns.append(PsqlColumn(item["name"], item["type"], item["is_nullable"], item.get("max_len", None)))
        return columns


class PsqlRow(ApiObject):

    def __init__(self, table_name, row_id, cols_and_values):
        self.table_name = table_name
        self.id = row_id
        self.values = cols_and_values

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in ["id", "values"])

    def __hash__(self):
        return hash((self.table_name, self.id))

    def __repr__(self):
        return "{} (table={}, id={})".format(self.__class__.__name__, self.table_name, self.id)

    @classmethod
    def post(cls, table_name, cols_and_values):
        request = requests.Request(method="POST", url="/tables/{}/rows".format(table_name), json=cols_and_values)
        row_id = cls.handle_request(request)["id"]
        return cls.get(table_name, row_id)

    @classmethod
    def get(cls, table_name, row_id):
        request = requests.Request(method="GET", url="/tables/{}/rows/{}".format(table_name, row_id))
        response = cls.handle_request(request)
        return cls(table_name, response["id"], response["values"])

    @classmethod
    def get_list(cls, table_name):
        request = requests.Request(method="GET", url="/tables/{}/rows".format(table_name))
        response = cls.handle_request(request)
        return [cls(table_name, item["id"], item["values"]) for item in response["rows"]]

    def put(self, cols_and_values):
        for new in cols_and_values:
            for col, old_value in self.values.items():
                if new["column_name"] == col:
                    self.values[col] = new["value"]
        request = requests.Request(method="PUT", url="/tables/{}/rows/{}".format(self.table_name, self.id),
                                   json=cols_and_values)
        self.handle_request(request)

    def delete(self):
        request = requests.Request(method="DELETE", url="/tables/{}/rows/{}".format(self.table_name, self.id))
        self.handle_request(request)

