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

"""
Tests in this module are functional tests of the rest api, and thus require the AUT to run.
"""

import unittest

import ddt
import requests

import unittests.common as common


class MainTestCase(unittest.TestCase):

    COLUMN_NAMES = ["col1", "col2", "col3"]
    COLUMN_JSON = [{"name": COLUMN_NAMES[0], "type": "VARCHAR", "max_len": 10},
                   {"name": COLUMN_NAMES[1], "type": "INTEGER"},
                   {"name": COLUMN_NAMES[2], "type": "BOOLEAN", "is_nullable": False}]

    def tearDown(self):
        for table in common.PsqlTable.TEST_TABLES:
            table.delete()

    def assertUnorderedListEqual(self, l1, l2):
        self.assertListEqual(sorted(l1), sorted(l2))


class Tables(MainTestCase):

    def test_create_table_with_columns(self):
        table_name = "hi"
        table = common.PsqlTable.post(table_name, self.COLUMN_JSON)
        expected_columns = [common.PsqlColumn.from_json_definition(c) for c in self.COLUMN_JSON]
        expected_columns.append(common.PsqlColumn("id", "INTEGER", False, None))
        columns = table.get_columns()
        self.assertTrue(all([c in columns for c in expected_columns]))

    def test_cannot_create_table_with_existing_name(self):
        table_name = "hi"
        common.PsqlTable.post(table_name, self.COLUMN_JSON)
        self.assertRaises(common.HTTPResponseError, common.PsqlTable.post, table_name, self.COLUMN_JSON)

    def test_cannot_create_table_with_identical_column_names(self):
        table_name = "hi"
        column_json = [{"name": "col", "type": "BOOLEAN"}, {"name": "col", "type": "INTEGER"}]
        self.assertRaises(common.HTTPResponseError, common.PsqlTable.post, table_name, column_json)


class RowsInEmptyTables(MainTestCase):

    def setUp(self):
        self.table_name = "oh_hai"
        common.PsqlTable.post(self.table_name, self.COLUMN_JSON)

    def test_get_rows_there_are_no_rows(self):
        rows = common.PsqlRow.get_list(self.table_name)
        self.assertEqual(rows, [])

    def test_get_not_existing_row(self):
        self.assertRaises(common.HTTPResponseError, common.PsqlRow.get, self.table_name, 1)


@ddt.ddt
class Rows(MainTestCase):

    COLUMN_NAMES = ["col1", "col2", "col3"]
    ROW_JSON = [[{"column_name": cn, "value": v} for cn, v in zip(COLUMN_NAMES, ["kitten", 12, False])],
                [{"column_name": cn, "value": v} for cn, v in zip(COLUMN_NAMES, [None, None, False])],
                [{"column_name": COLUMN_NAMES[2], "value": True}]]

    def setUp(self):
        self.table_name = "oh_hai"
        common.PsqlTable.post(self.table_name, self.COLUMN_JSON)
        self.rows = [common.PsqlRow.post(self.table_name, rj) for rj in self.ROW_JSON]

    def test_get_not_existing_row(self):
        self.assertRaises(common.HTTPResponseError, common.PsqlRow.get, self.table_name, len(self.ROW_JSON) + 2)

    @ddt.data(*range(1, len(ROW_JSON) + 1))
    def test_get_row(self, row_id):
        row = common.PsqlRow.get(self.table_name, row_id)
        self.assertEqual(row, self.rows[row_id-1])

    def test_delete_row(self):
        self.rows[1].delete()
        rows = common.PsqlRow.get_list(self.table_name)
        self.assertNotIn(self.rows[1], rows)

    @ddt.data((1, [{"column_name": COLUMN_NAMES[0], "value": None}]),
              (1, [{"column_name": COLUMN_NAMES[1], "value": None}]),
              (1, [{"column_name": COLUMN_NAMES[0], "value": None},
                   {"column_name": COLUMN_NAMES[1], "value": None}]),
              (2, [{"column_name": COLUMN_NAMES[0], "value": "kitten"},
                   {"column_name": COLUMN_NAMES[2], "value": True}]),
              (2, [{"column_name": cn, "value": v} for cn, v in zip(COLUMN_NAMES, ["kitten", None, True])]),
              (3, [{"column_name": cn, "value": v} for cn, v in zip(COLUMN_NAMES, ["kitten", 42, False])]))
    @ddt.unpack
    def test_put_row(self, row_id, put_values):
        self.rows[row_id-1].put(put_values)
        row = common.PsqlRow.get(self.table_name, row_id)
        self.assertEqual(row, self.rows[row_id-1])


class UnsupportedMethods(MainTestCase):
    # TODO expand this test class

    def test_incorrect_method_on_tables(self):
        request = requests.Request(method="PUT", url="/tables")
        self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)


@ddt.ddt
class InvalidPaths(MainTestCase):
    """Test validation of path variables"""

    @ddt.data(*common.INVALID_LABELS)
    def test_invalid_string_in_post_table(self, invalid_string):
        body = {"table_name": "table_1", "columns": [{"name": "col1", "type": "varchar", "len": [1]}]}
        request = requests.Request(method="POST", url="/tables".format(invalid_string), json=body)
        self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)

    @ddt.data(*common.INVALID_LABELS)
    def test_invalid_string_in_get_table(self, invalid_string):
        request = requests.Request(method="GET", url="/tables/{}".format(invalid_string))
        self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)

    @ddt.data(*common.INVALID_LABELS)
    def test_invalid_string_in_delete_table(self, invalid_string):
        request = requests.Request(method="DELETE", url="/tables/{}".format(invalid_string))
        self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)

    @ddt.data(*common.INVALID_LABELS)
    def test_invalid_string_in_get_rows(self, invalid_string):
        request = requests.Request(method="GET", url="/tables/{}/rows".format(invalid_string))
        self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)

    @ddt.data(*common.INVALID_LABELS)
    def test_invalid_string_in_post_row(self, invalid_string):
        body = [{"column_name": "col1", "value": 123}]
        request = requests.Request(method="POST", url="/tables/{}/rows".format(invalid_string), json=body)
        self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)

    @ddt.data(*common.INVALID_LABELS)
    def test_invalid_table_in_get_put_delete_row(self, invalid_string):
        invalid_url = "/tables/{}/rows/ok_row".format(invalid_string)
        for method in ["GET", "PUT", "DELETE"]:
            request = requests.Request(method=method, url=invalid_url)
            self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)

    @ddt.data(*(common.INVALID_LABELS + ["sss"]))
    def test_invalid_row_in_get_put_delete_row(self, invalid_string):
        invalid_url = "/tables/ok_table_name/rows/{}".format(invalid_string)
        for method in ["GET", "PUT", "DELETE"]:
            request = requests.Request(method=method, url=invalid_url)
            self.assertRaises(common.HTTPResponseError, common.ApiObject.handle_request, request)
