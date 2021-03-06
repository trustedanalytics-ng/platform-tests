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
from modules.service_tools.db import Table, Column, Row
from modules.test_names import generate_test_object_name
from tests.fixtures.db_input import DbInput

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


class TestMysqlAndPsql(object):
    app = None
    test_table_name = DbInput.test_table_name
    test_columns = DbInput.test_columns
    mysql_specyfic_columns = DbInput.mysql_specyfic_test_columns
    row_value_list = DbInput.test_rows_1

    @pytest.fixture(scope="module")
    def db_type(self, app_bound_psql, app_bound_mysql):
        return {
            "app_bound_psql": app_bound_psql,
            "app_bound_mysql": app_bound_mysql,
        }

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_mysql_tables(self, request):
        def fin():
            for table in Table.TABLES:
                table.delete()

        request.addfinalizer(fin)

    def _create_expected_row(self, app, table_name, id, expected_values):
        values = {col["column_name"]: col["value"] for col in expected_values}
        values.update({col["name"]: None for col in self.test_columns if col["name"] not in values.keys()})
        return Row(app, table_name, id, values)

    def _get_expected_rows(self, app):
        expected_rows = []
        for row_value in self.row_value_list:
            id = Row.post(app, self.test_table_name, row_value)
            expected_rows.append(self._create_expected_row(app, self.test_table_name, id, row_value))
        return expected_rows

    @pytest.mark.bugs("DPNG-15095 Unable to create mysql instance - error: inappropriate state OFFLINE")
    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_bound_mysql", "app_bound_psql"))
    def test_create_and_delete_table(self, db_type, db_type_key):
        """
        <b>Description:</b>
        Checks if a table can be created and deleted.

        <b>Input data:</b>
        1. sql-api-example app with bound database

        <b>Expected results:</b>
        A table was created and then deleted.

        <b>Steps:</b>
        1. Create a table.
        2. Verify the table was created.
        3. Delete the table.
        4. Verify the table was deleted.
        """
        app = db_type[db_type_key]
        self.__class__.test_table_name = generate_test_object_name(prefix=DbInput.test_table_name)
        test_table = Table.post(app, self.test_table_name, self.test_columns)
        table_list = Table.get_list(app)
        assert test_table in table_list
        test_table.delete()
        table_list = Table.get_list(app)
        assert test_table not in table_list

    @pytest.mark.bugs("DPNG-15095 Unable to create mysql instance - error: inappropriate state OFFLINE")
    @priority.medium
    def test_get_table_columns_msql(self, db_type):
        """
        <b>Description:</b>
        Checks if a table with columns can be created.

        <b>Input data:</b>
        1. sql-api-example app with bound database

        <b>Expected results:</b>
        A table was created and has columns.

        <b>Steps:</b>
        1. Create a table with columns.
        2. Verify columns were created.
        """
        app = db_type["app_bound_mysql"]
        test_table = Table.post(app, self.test_table_name, self.test_columns)
        expected_columns = [Column.from_json_definition(c) for c in self.mysql_specyfic_columns]
        expected_columns.append(Column("id", "BIGINT", False, 20))
        columns = test_table.get_columns()
        assert len(columns) == len(expected_columns)
        for column in expected_columns:
            assert column in columns

    @priority.medium
    def test_get_table_columns_psql(self, db_type):
        """
        <b>Description:</b>
        Checks if a table with columns can be created.

        <b>Input data:</b>
        1. sql-api-example app with bound database

        <b>Expected results:</b>
        A table was created and has columns.

        <b>Steps:</b>
        1. Create a table with columns.
        2. Verify columns were created.
        """
        app = db_type["app_bound_psql"]
        test_table = Table.post(app, self.test_table_name, self.test_columns)
        expected_columns = [Column.from_json_definition(c) for c in self.test_columns]
        expected_columns.append(Column("id", "INTEGER", False, None))
        columns = test_table.get_columns()
        assert len(columns) == len(expected_columns)
        for column in expected_columns:
            assert column in columns

    @pytest.mark.bugs("DPNG-15095 Unable to create mysql instance - error: inappropriate state OFFLINE")
    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_bound_mysql", "app_bound_psql"))
    @pytest.mark.parametrize("row_values", row_value_list)
    def test_post_row(self, db_type, db_type_key, row_values):
        """
        <b>Description:</b>
        Checks if a row can be inserted.

        <b>Input data:</b>
        1. sql-api-example app with bound database

        <b>Expected results:</b>
        A table with a row.

        <b>Steps:</b>
        1. Create a table.
        2. Insert a row.
        3. Verify a row was inserted.
        """
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        new_row_id = Row.post(app, self.test_table_name, row_values)
        expected_row = self._create_expected_row(app, self.test_table_name, new_row_id, row_values)
        row_list = Row.get_list(app, self.test_table_name)
        assert expected_row in row_list
        row = Row.get(app, self.test_table_name, row_id=1)
        assert row == expected_row

    @pytest.mark.bugs("DPNG-15095 Unable to create mysql instance - error: inappropriate state OFFLINE")
    @priority.low
    @pytest.mark.parametrize("db_type_key", ("app_bound_mysql", "app_bound_psql"))
    def test_post_multiple_rows(self, db_type, db_type_key):
        """
        <b>Description:</b>
        Checks if a multiple rows can be inserted.

        <b>Input data:</b>
        1. sql-api-example app with bound database

        <b>Expected results:</b>
        A table with multiple rows inserted.

        <b>Steps:</b>
        1. Create a table.
        2. Insert multiple rows.
        3. Verify a row was inserted.
        """
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows(app)
        rows = Row.get_list(app, self.test_table_name)
        assert rows == expected_rows

    @pytest.mark.bugs("DPNG-15095 Unable to create mysql instance - error: inappropriate state OFFLINE")
    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_bound_mysql", "app_bound_psql"))
    def test_put_row(self, db_type, db_type_key):
        """
        <b>Description:</b>
        Checks if a row can be updated.

        <b>Input data:</b>
        1. sql-api-example app with bound database

        <b>Expected results:</b>
        A table with a updated row.

        <b>Steps:</b>
        1. Create a table.
        2. Insert multiple rows with test data.
        3. Update a row.
        4. Verify a row was updated.
        """
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows(app)
        new_values = [{"column_name": "col0", "value": self.test_table_name}, {"column_name": "col2", "value": True}]
        expected_rows[1].put(new_values)
        row = Row.get(app, self.test_table_name, row_id=expected_rows[1].id)
        assert expected_rows[1] == row

    @pytest.mark.bugs("DPNG-15095 Unable to create mysql instance - error: inappropriate state OFFLINE")
    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_bound_mysql", "app_bound_psql"))
    def test_delete_row(self, db_type, db_type_key):
        """
        <b>Description:</b>
        Checks if a row can be deleted.

        <b>Input data:</b>
        1. sql-api-example app with bound database

        <b>Expected results:</b>
        A table with a deleted row.

        <b>Steps:</b>
        1. Create a table.
        2. Insert multiple rows.
        3. Delete a row.
        4. Verify a row was deleted.
        """
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        posted_rows = self._get_expected_rows(app)
        posted_rows[1].delete()
        rows = Row.get_list(app, self.test_table_name)
        assert posted_rows[1] not in rows
