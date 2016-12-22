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

class DbInput:
    test_table_name = "oh_hai"

    test_columns = [
        {"name": "col0", "type": "VARCHAR", "max_len": 60},
        {"name": "col1", "type": "INTEGER", "is_nullable": False},
        {"name": "col2", "type": "BOOLEAN", "is_nullable": True}
    ]

    mysql_specyfic_test_columns = [
        {"name": "col0", "type": "VARCHAR", "max_len": 60},
        {"name": "col1", "type": "INTEGER", "max_len": 11, "is_nullable": False},
        {"name": "col2", "type": "TINYINT", "max_len": 1, "is_nullable": True}
    ]

    test_rows_0 = [
        [
            {"column_name": "col0", "value": "kitten"},
            {"column_name": "col1", "value": 42},
            {"column_name": "col2", "value": True}
        ],
        [
            {"column_name": "col0", "value": "doggy"},
            {"column_name": "col1", "value": 42},
            {"column_name": "col2", "value": True}
        ]
    ]

    test_rows_1 = [
        test_rows_0[0],
        [
            {"column_name": "col1", "value": 0}
        ],
        [
            {"column_name": "col0", "value": None},
            {"column_name": "col1", "value": 9000},
            {"column_name": "col2", "value": None}
        ]
    ]
