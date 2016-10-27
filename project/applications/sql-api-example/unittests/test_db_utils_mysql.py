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
from sqlalchemy.exc import OperationalError


COL_NAMES = ["col1", "col2", "col3"]
COLUMNS = [{"name": COL_NAMES[0], "type": "integer"},
           {"name": COL_NAMES[1], "type": "varchar", "max_len": 10},
           {"name": COL_NAMES[2], "type": "integer", "is_nullable": False}]


@ddt.ddt
class MysqlSpecificTests(unittest.TestCase):

    TEST_TABLES = []
    
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseClient()

    def setUp(self):
        self.table_name = "oh_hai"
        table = self.db.create_table(table_name=self.table_name, columns=COLUMNS)
        self.TEST_TABLES.append(table)

    def tearDown(self):
        while len(self.TEST_TABLES) > 0:
            table = self.TEST_TABLES.pop()
            self.db.delete_table(table)

    @ddt.data({COL_NAMES[0]: 1, COL_NAMES[1]: "kitty", COL_NAMES[2]: None},
              {COL_NAMES[0]: 1, COL_NAMES[1]: "kitty"},
              {})
    def test_cannot_post_null_to_not_null_columns(self, values):
        self.assertRaises(OperationalError, self.db.add_row, table_name=self.table_name, values_dict=values)

    def test_cannot_put_string_to_integer_type_column(self):
        updated_values = {COL_NAMES[0]: "sss"}
        self.assertRaises(OperationalError, self.db.update_row, self.table_name, 1, updated_values)
