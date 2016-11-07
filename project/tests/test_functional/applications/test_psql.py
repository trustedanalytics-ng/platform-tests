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

import pytest

from modules.constants import TapComponent as TAP
from modules.markers import priority
from modules.service_tools.psql import PsqlTable, PsqlColumn, PsqlRow
from modules.test_names import generate_test_object_name
from tests.fixtures.db_input import DbInput

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestPsql(object):
    psql_app = None
    test_table_name = DbInput.test_table_name
    test_columns = DbInput.test_columns
    row_value_list = DbInput.test_rows_1

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_psql_tables(self, request):
        def fin():
            for table in PsqlTable.TABLES:
                table.delete()

        request.addfinalizer(fin)

    def _create_expected_row(self, psql_app, table_name, id, expected_values):
        values = {col["column_name"]: col["value"] for col in expected_values}
        values.update({col["name"]: None for col in self.test_columns if col["name"] not in values.keys()})
        return PsqlRow(psql_app, table_name, id, values)

    def _get_expected_rows(self, psql_app):
        expected_rows = []
        for row_value in self.row_value_list:
            id = PsqlRow.post(psql_app, self.test_table_name, row_value)
            expected_rows.append(self._create_expected_row(psql_app, self.test_table_name, id, row_value))
        return expected_rows

    @priority.medium
    def test_create_and_delete_table(self, psql_app):
        self.__class__.test_table_name = generate_test_object_name(prefix=DbInput.test_table_name)
        test_table = PsqlTable.post(psql_app, self.test_table_name, self.test_columns)
        table_list = PsqlTable.get_list(psql_app)
        assert test_table in table_list
        test_table.delete()
        table_list = PsqlTable.get_list(psql_app)
        assert test_table not in table_list

    @priority.medium
    def test_get_table_columns(self, psql_app):
        test_table = PsqlTable.post(psql_app, self.test_table_name, self.test_columns)
        expected_columns = [PsqlColumn.from_json_definition(c) for c in self.test_columns]
        expected_columns.append(PsqlColumn("id", "INTEGER", False, None))
        columns = test_table.get_columns()
        assert len(columns) == len(expected_columns)
        for column in expected_columns:
            assert column in columns

    @priority.medium
    @pytest.mark.parametrize("row_values", row_value_list)
    def test_post_row(self, row_values, psql_app):
        PsqlTable.post(psql_app, self.test_table_name, self.test_columns)
        new_row_id = PsqlRow.post(psql_app, self.test_table_name, row_values)
        expected_row = self._create_expected_row(psql_app, self.test_table_name, new_row_id, row_values)
        row_list = PsqlRow.get_list(psql_app, self.test_table_name)
        assert expected_row in row_list
        row = PsqlRow.get(psql_app, self.test_table_name, row_id=1)
        assert row == expected_row

    @priority.low
    def test_post_multiple_rows(self, psql_app):
        PsqlTable.post(psql_app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows(psql_app)
        rows = PsqlRow.get_list(psql_app, self.test_table_name)
        assert rows == expected_rows

    @priority.medium
    def test_put_row(self, psql_app):
        PsqlTable.post(psql_app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows(psql_app)
        new_values = [{"column_name": "col0", "value": self.test_table_name}, {"column_name": "col2", "value": True}]
        expected_rows[1].put(new_values)
        row = PsqlRow.get(psql_app, self.test_table_name, row_id=expected_rows[1].id)
        assert expected_rows[1] == row

    @priority.medium
    def test_delete_row(self, psql_app):
        PsqlTable.post(psql_app, self.test_table_name, self.test_columns)
        posted_rows = self._get_expected_rows(psql_app)
        posted_rows[1].delete()
        rows = PsqlRow.get_list(psql_app, self.test_table_name)
        assert posted_rows[1] not in rows
