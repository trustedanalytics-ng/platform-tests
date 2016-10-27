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

from app.db_utils import DatabaseClient
from sqlalchemy.exc import NoSuchTableError, DataError, CompileError, DatabaseError, IntegrityError, ProgrammingError, \
    OperationalError




COL_NAMES = ["col1", "col2", "col3"]
COLUMNS = [{"name": COL_NAMES[0], "type": "integer"},
           {"name": COL_NAMES[1], "type": "varchar", "max_len": 10},
           {"name": COL_NAMES[2], "type": "integer", "is_nullable": False}]
CORRECT_ROW_VALUES = [{COL_NAMES[0]: 1, COL_NAMES[1]: "oh hai", COL_NAMES[2]: 2147483647},
                      {COL_NAMES[1]: "kitty", COL_NAMES[2]: -2147483648},
                      {COL_NAMES[0]: None, COL_NAMES[1]: "k, thx bye", COL_NAMES[2]: -2147483648},
                      {COL_NAMES[2]: 12345}]


class BaseTest(unittest.TestCase):

    TEST_TABLES = []
    
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseClient()

    def tearDown(self):
        while len(self.TEST_TABLES) > 0:
            table = self.TEST_TABLES.pop()
            self.db.delete_table(table)

    def _get_expected_row_values(self, values):
        return {cn: values.get(cn) for cn in COL_NAMES}


class Tables(BaseTest):

    def assertColumnsEqual(self, column, expected_column):
        self.assertEqual(column["name"], expected_column["name"])
        self.assertEqual(column["type"].lower(), expected_column["type"].lower())

    def test_create_simple_table(self):
        expected_table = self.db.create_table(table_name="test_1", columns=COLUMNS)
        self.TEST_TABLES.append(expected_table)
        tables = self.db.get_table_list()
        table = [t for t in tables if t == expected_table]
        self.assertEqual(len(table), 1)
        columns = self.db.get_columns(expected_table)
        for ec in [col for col in columns if col["name"] != "id"]:
            cc = next((c for c in COLUMNS if c["name"] == ec["name"]), None)
            self.assertColumnsEqual(cc, ec)

    def test_create_table_no_columns(self):
        expected_table = self.db.create_table(table_name="test_2", columns=[])
        self.TEST_TABLES.append(expected_table)
        columns = self.db.get_columns(expected_table)
        self.assertEqual(len(columns), 1)  # column id is always declared

    def test_delete_table(self):
        deleted_table = self.db.create_table(table_name="test_3", columns=[])
        self.db.delete_table(deleted_table)
        tables = self.db.get_table_list()
        self.assertNotIn(deleted_table, tables, "Table was not deleted")


@ddt.ddt
class RowsPostGet(BaseTest):

    def setUp(self):
        self.table_name = "oh_hai"
        table = self.db.create_table(table_name=self.table_name, columns=COLUMNS)
        self.TEST_TABLES.append(table)

    def test_get_rows_no_rows(self):
        rows = self.db.get_rows(self.table_name)
        self.assertEqual(rows, [])

    @ddt.data(*CORRECT_ROW_VALUES)
    def test_get_rows_one_row(self, expected_values):
        self.db.add_row(table_name=self.table_name, values_dict=expected_values)
        expected_values = self._get_expected_row_values(expected_values)
        rows = self.db.get_rows(table_name=self.table_name)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["values"], expected_values)

    def test_get_rows_many_rows(self):
        for values in CORRECT_ROW_VALUES:
            self.db.add_row(table_name=self.table_name, values_dict=values)
        rows = self.db.get_rows(table_name=self.table_name)
        self.assertEqual(len(rows), len(CORRECT_ROW_VALUES))
        for i, (row, values) in list(enumerate(zip(rows, CORRECT_ROW_VALUES))):
            self.assertEqual(row["values"], self._get_expected_row_values(values))

    @ddt.data(*CORRECT_ROW_VALUES)
    def test_post_rows(self, values):
        row_id = self.db.add_row(table_name=self.table_name, values_dict=values)["id"]
        row = self.db.get_row(self.table_name, row_id)
        self.assertEqual(row["values"], self._get_expected_row_values(values))

    @ddt.data({COL_NAMES[0]: 123, COL_NAMES[1]: "oh hai", COL_NAMES[2]: 2147483648},
              {COL_NAMES[0]: 42, COL_NAMES[1]: "thx bye", COL_NAMES[2]: -2147483649},
              {COL_NAMES[0]: 42, COL_NAMES[1]: "i'm tooooo long", COL_NAMES[2]: 12})
    def test_cannot_post_incorrect_rows(self, values):
        self.assertRaises(DataError, self.db.add_row, table_name=self.table_name, values_dict=values)

    def test_cannot_post_data_to_non_existing_columns(self):
        values = {COL_NAMES[2]: 12345, "extra": None}
        self.assertRaises(CompileError, self.db.add_row, table_name=self.table_name, values_dict=values)

    @ddt.data(*CORRECT_ROW_VALUES)
    def test_get_row_from_table_with_single_row(self, expected_values):
        self.db.add_row(table_name=self.table_name, values_dict=expected_values)
        expected_values = self._get_expected_row_values(expected_values)
        row = self.db.get_row(table_name=self.table_name, row_id=1)
        self.assertEqual(row["values"], expected_values)

    @ddt.data(*range(1, len(CORRECT_ROW_VALUES) + 1))  # psql indexing starts with 1
    def test_get_row_from_table_with_many_rows(self, row_id):
        for values in CORRECT_ROW_VALUES:
            self.db.add_row(table_name=self.table_name, values_dict=values)
        row = self.db.get_row(table_name=self.table_name, row_id=row_id)
        self.assertEqual(row["values"], self._get_expected_row_values(CORRECT_ROW_VALUES[row_id - 1]))

    def test_get_non_existing_row(self):
        for values in CORRECT_ROW_VALUES:
            self.db.add_row(table_name=self.table_name, values_dict=values)
        row = self.db.get_row(table_name=self.table_name, row_id=len(CORRECT_ROW_VALUES) + 1)
        self.assertIsNone(row)

    def test_cannot_get_row_from_non_existing_table(self):
        self.assertRaises(NoSuchTableError, self.db.get_row, table_name="xzxx", row_id=1)


@ddt.ddt
class RowsPutDelete(BaseTest):

    def setUp(self):
        self.table_name = "oh_hai"
        table = self.db.create_table(table_name=self.table_name, columns=COLUMNS)
        self.TEST_TABLES.append(table)
        rows_id = [self.db.add_row(self.table_name, row_values)["id"] for row_values in CORRECT_ROW_VALUES]
        self.rows = [self.db.get_row(self.table_name, row_id) for row_id in rows_id]

    @ddt.data({COL_NAMES[0]: 4},
              {COL_NAMES[1]: "hihi"},
              {COL_NAMES[2]: 42},
              {COL_NAMES[0]: None, COL_NAMES[1]: None},
              {COL_NAMES[0]: 1, COL_NAMES[1]: "kitty", COL_NAMES[2]: 0})
    def test_put_row(self, updated_values):
        test_row = 0
        test_row_id = self.rows[test_row]["id"]
        original_values = self.rows[test_row]["values"]
        expected_values = self._get_expected_row_values(original_values)
        expected_values.update(updated_values)
        self.db.update_row(self.table_name, test_row_id, updated_values)
        updated_row = self.db.get_row(self.table_name, test_row_id)
        self.assertEqual(updated_row["id"], test_row_id)
        self.assertEqual(updated_row["values"], expected_values)
        updated_row = self.db.get_row(self.table_name, test_row_id)
        self.assertEqual(updated_row["id"], test_row_id)
        self.assertEqual(updated_row["values"], expected_values)

    def test_put_incorrect_row(self):
        updated_values = {COL_NAMES[2]: None}
        self.assertRaises(DatabaseError, self.db.update_row, self.table_name, 1, updated_values)

    def test_cannot_put_empty_data(self):
        updated_values = {}
        self.assertRaises(ProgrammingError, self.db.update_row, self.table_name, 1, updated_values)

    def test_cannot_put_data_to_non_existing_column(self):
        updated_values = {"xyz": "abc"}
        self.assertRaises(CompileError, self.db.update_row, self.table_name, 1, updated_values)

    def test_delete_single_row(self):
        self.db.delete_row(self.table_name, self.rows[0]["id"])
        deleted_row = self.db.get_row(table_name=self.table_name, row_id=self.rows[0]["id"])
        self.assertIsNone(deleted_row)

    def test_delete_all_rows(self):
        for row in self.rows:
            self.db.delete_row(self.table_name, row["id"])
        rows = self.db.get_rows(self.table_name)
        self.assertEqual(len(rows), 0)

    def test_delete_non_existing_row(self):
        row_id = len(self.rows) + 5
        self.db.delete_row(self.table_name, row_id=row_id)

    def test_cannot_delete_from_non_existing_table(self):
        self.assertRaises(NoSuchTableError, self.db.delete_row, "xyz", row_id=1)



