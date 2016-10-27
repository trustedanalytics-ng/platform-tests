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

import unittest

import ddt
from werkzeug.exceptions import BadRequest

from app import input_validation
import unittests.common as common


@ddt.ddt
class RequestBodyValidation(unittest.TestCase):

    @ddt.data({"table_name": "table_1",
               "columns": [{"name": "col1", "type": "varchar", "max_len": 255},
                           {"name": "col2", "type": "integer"},
                           {"name": "col2", "type": "boolean", "is_nullable": False},
                           {"name": "col2", "type": "char", "is_nullable": True, "max_len": 2}]})
    def test_post_tables_correct(self, body):
        self.assertIsNone(input_validation.validate_post_tables(body))

    @ddt.data({"table_name": 123},
              {"table_name": "table_2"},
              {"extra_item": 42},
              {"table_name": "table_3", "columns": []},
              {"table_name": "table_1", "columns": "sssss"},
              {"table_name": "table_1", "columns": 123},
              {"table_name": "table_1", "columns": {"hi": "there"}},
              {"table_name": "table_1", "columns": [{"type": "test", "max_len": 1}]},
              {"table_name": "table_1", "columns": [{"name": 123, "type": "test", "max_len": 1}]},
              {"table_name": "table_1", "columns": [{"name": "test", "max_len": 1}]},
              {"table_name": "table_1", "columns": [{"name": "col1", "type": "char", "extra": 1}]},
              {"table_name": "table_1", "columns": [{"name": "col1", "type": "char", "max_len": "a"}]},
              {"table_name": "table_1", "columns": [{"name": "col1", "type": "char", "is_nullable": 0}]},
              {"table_name": "table_1", "columns": [{"name": "col1", "type": "char", "is_nullable": "a"}]})
    def test_post_tables_incorrect_schema(self, body):
        self.assertRaises(BadRequest, input_validation.validate_post_tables, body)

    @ddt.data(*common.INVALID_LABELS)
    def test_post_tables_incorrect_table_name(self, invalid_string):
        body = {"table_name": invalid_string}
        self.assertRaises(BadRequest, input_validation.validate_post_tables, body)

    @ddt.data(*common.INVALID_LABELS)
    def test_post_tables_incorrect_column_name(self, invalid_string):
        body = {"table_name": "table_1", "columns": [{"name": invalid_string, "type": "varchar"}]}
        self.assertRaises(BadRequest, input_validation.validate_post_tables, body)

    @ddt.data(*common.INVALID_TYPES)
    def test_post_tables_incorrect_data_type(self, invalid_string):
        body = {"table_name": "table_1", "columns": [{"name": "col1", "type": invalid_string}]}
        self.assertRaises(BadRequest, input_validation.validate_post_tables, body)

    @ddt.data([{"column_name": "col1", "value": 123}],
              [{"column_name": "col1", "value": "str"}],
              [{"column_name": "col1", "value": None}],
              [{"column_name": "col1", "value": ""}],
              [{"column_name": "col1", "value": 123}, {"column_name": "col2", "value": "hi"},
               {"column_name": "col3", "value": 0}, {"column_name": "col4", "value": "hi there"}])
    def test_post_rows_correct(self, body):
        self.assertIsNone(input_validation.validate_put_post_row(body))

    @ddt.data({"column_name": "col1", "value": 123},
              [{"column_name": 1234, "value": 123}],
              [{"column_name": "col1", "value": {}}],
              [])
    def test_post_rows_incorrect_schema(self, body):
        self.assertRaises(BadRequest, input_validation.validate_put_post_row, body)

    @ddt.data(*common.INVALID_LABELS)
    def test_post_rows_incorrect_column_name(self, invalid_string):
        body = [{"column_name": invalid_string, "value": 123}]
        self.assertRaises(BadRequest, input_validation.validate_post_tables, body)

    @ddt.data([{"column_name": "col1", "value": 123}],
              [{"column_name": "col1", "value": "str"}],
              [{"column_name": "col1", "value": None}],
              [{"column_name": "col1", "value": ""}],
              [{"column_name": "col1", "value": "hi"}],
              [{"column_name": "col1", "value": "hi"}, {"column_name": "col2", "value": "hi"},
               {"column_name": "col3", "value": 4}])
    def test_put_row_correct(self, body):
        self.assertIsNone(input_validation.validate_put_post_row(body))

    @ddt.data({"values": [{"column_name": "col1", "value": 42}]},
              {"row_id": "id", "values": [{"column_name": "col1", "value": 42}]},
              {"row_id": 42},
              {"row_id": 12, "values": []})
    def test_put_row_incorrect_schema(self, body):
        self.assertRaises(BadRequest, input_validation.validate_put_post_row, body)

    @ddt.data(*common.INVALID_LABELS)
    def test_put_row_incorrect_column_name(self, invalid_string):
        body = {"row_id": 1, "values": [{"column_name": invalid_string, "value": 123}]}
        self.assertRaises(BadRequest, input_validation.validate_post_tables, body)

    @ddt.data(*(common.INVALID_LABELS + ["abc"]))
    def test_delete_row_incorrect_row_id(self, invalid_string):
        self.assertRaises(BadRequest, input_validation.validate_integer, invalid_string)
