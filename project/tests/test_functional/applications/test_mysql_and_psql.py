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
    def db_type(self, app_binded_psql, app_binded_mysql):
        return {
            "app_binded_psql": app_binded_psql,
            "app_binded_mysql": app_binded_mysql
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

    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_binded_mysql", "app_binded_psql"))
    @pytest.mark.bugs("DPNG-12912 TAP NG - offering naming unification & new plans")
    @pytest.mark.bugs("DPNG-12956 Applications are not packed before push action in platform tests")
    def test_create_and_delete_table(self, db_type, db_type_key):
        app = db_type[db_type_key]
        self.__class__.test_table_name = generate_test_object_name(prefix=DbInput.test_table_name)
        test_table = Table.post(app, self.test_table_name, self.test_columns)
        table_list = Table.get_list(app)
        assert test_table in table_list
        test_table.delete()
        table_list = Table.get_list(app)
        assert test_table not in table_list

    @priority.medium
    @pytest.mark.bugs("DPNG-12912 TAP NG - offering naming unification & new plans")
    @pytest.mark.bugs("DPNG-12956 Applications are not packed before push action in platform tests")
    def test_get_table_columns_msql(self, db_type):
        app = db_type["app_binded_mysql"]
        test_table = Table.post(app, self.test_table_name, self.test_columns)
        expected_columns = [Column.from_json_definition(c) for c in self.mysql_specyfic_columns]
        expected_columns.append(Column("id", "BIGINT", False, 20))
        columns = test_table.get_columns()
        assert len(columns) == len(expected_columns)
        for column in expected_columns:
            assert column in columns

    @priority.medium
    @pytest.mark.bugs("DPNG-12912 TAP NG - offering naming unification & new plans")
    @pytest.mark.bugs("DPNG-12956 Applications are not packed before push action in platform tests")
    def test_get_table_columns_psql(self, db_type):
        app = db_type["app_binded_psql"]
        test_table = Table.post(app, self.test_table_name, self.test_columns)
        expected_columns = [Column.from_json_definition(c) for c in self.test_columns]
        expected_columns.append(Column("id", "INTEGER", False, None))
        columns = test_table.get_columns()
        assert len(columns) == len(expected_columns)
        for column in expected_columns:
            assert column in columns

    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_binded_mysql", "app_binded_psql"))
    @pytest.mark.parametrize("row_values", row_value_list)
    @pytest.mark.bugs("DPNG-12912 TAP NG - offering naming unification & new plans")
    @pytest.mark.bugs("DPNG-12956 Applications are not packed before push action in platform tests")
    def test_post_row(self, row_values, db_type, db_type_key):
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        new_row_id = Row.post(app, self.test_table_name, row_values)
        expected_row = self._create_expected_row(app, self.test_table_name, new_row_id, row_values)
        row_list = Row.get_list(app, self.test_table_name)
        assert expected_row in row_list
        row = Row.get(app, self.test_table_name, row_id=1)
        assert row == expected_row

    @priority.low
    @pytest.mark.parametrize("db_type_key", ("app_binded_mysql", "app_binded_psql"))
    @pytest.mark.bugs("DPNG-12912 TAP NG - offering naming unification & new plans")
    @pytest.mark.bugs("DPNG-12956 Applications are not packed before push action in platform tests")
    def test_post_multiple_rows(self, db_type, db_type_key):
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows(app)
        rows = Row.get_list(app, self.test_table_name)
        assert rows == expected_rows

    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_binded_mysql", "app_binded_psql"))
    @pytest.mark.bugs("DPNG-12912 TAP NG - offering naming unification & new plans")
    @pytest.mark.bugs("DPNG-12956 Applications are not packed before push action in platform tests")
    def test_put_row(self, db_type, db_type_key):
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows(app)
        new_values = [{"column_name": "col0", "value": self.test_table_name}, {"column_name": "col2", "value": True}]
        expected_rows[1].put(new_values)
        row = Row.get(app, self.test_table_name, row_id=expected_rows[1].id)
        assert expected_rows[1] == row

    @priority.medium
    @pytest.mark.parametrize("db_type_key", ("app_binded_mysql", "app_binded_psql"))
    @pytest.mark.bugs("DPNG-12912 TAP NG - offering naming unification & new plans")
    @pytest.mark.bugs("DPNG-12956 Applications are not packed before push action in platform tests")
    def test_delete_row(self, db_type, db_type_key):
        app = db_type[db_type_key]
        Table.post(app, self.test_table_name, self.test_columns)
        posted_rows = self._get_expected_rows(app)
        posted_rows[1].delete()
        rows = Row.get_list(app, self.test_table_name)
        assert posted_rows[1] not in rows
