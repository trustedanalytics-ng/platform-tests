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

from collections import namedtuple


class Column(namedtuple("Column", ["name", "data_type", "is_nullable", "max_len"])):

    def __new__(cls, name, data_type, is_nullable=None, max_len=None):
        is_nullable = True if is_nullable is None else is_nullable
        return super().__new__(cls, name, data_type, is_nullable, max_len)

    @classmethod
    def from_json_definition(cls, column_json):
        return cls(
            column_json["name"],
            column_json["type"],
            column_json.get("is_nullable"),
            column_json.get("max_len")
        )


class Table(namedtuple("Table", ["app", "name"])):

    TABLES = []

    @classmethod
    def post(cls, app, table_name, column_json):
        body = {"table_name": table_name, "columns": column_json}
        app.api_request(method="POST", path="tables", body=body)
        table = cls(app, table_name)
        cls.TABLES.append(table)
        return table

    @classmethod
    def get_list(cls, app):
        response = app.api_request(method="GET", path="tables")
        tables = []
        for name in response["tables"]:
            tables.append(cls(app, name))
        return tables

    def delete(self):
        self.app.api_request(method="DELETE", path="tables/{}".format(self.name))
        self.TABLES.remove(self)

    def get_columns(self):
        response = self.app.api_request(method="GET", path="tables/{}/columns".format(self.name))
        columns = []
        for item in response["columns"]:
            columns.append(Column(item["name"], item["type"], item.get("is_nullable"), item.get("max_len")))
        return columns


class Row(namedtuple("Row", ["app", "table_name", "id", "values"])):

    PATH_TO_ROW = "tables/{}/rows/{}"
    PATH_TO_ROWS = "tables/{}/rows"

    @classmethod
    def post(cls, app, table_name, cols_and_values):
        response = app.api_request(method="POST", path=cls.PATH_TO_ROWS.format(table_name),
                                   body=cols_and_values)
        return response["id"]

    @classmethod
    def get(cls, app, table_name, row_id):
        response = app.api_request(method="GET", path=cls.PATH_TO_ROW.format(table_name, row_id))
        return cls(app, table_name, response["id"], response["values"])

    @classmethod
    def get_list(cls, app, table_name):
        response = app.api_request(method="GET", path=cls.PATH_TO_ROWS.format(table_name))
        return [cls(app, table_name, item["id"], item["values"]) for item in response["rows"]]

    def put(self, cols_and_values):
        for new in cols_and_values:
            self.values[new["column_name"]] = new["value"]
        self.app.api_request(method="PUT", path=self.PATH_TO_ROW.format(self.table_name, self.id),
                             body=cols_and_values)

    def delete(self):
        self.app.api_request(method="DELETE", path=self.PATH_TO_ROW.format(self.table_name, self.id))
