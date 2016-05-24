#
# Copyright (c) 2015-2016 Intel Corporation
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

from modules import app_sources
from configuration import config
from modules.constants import ServiceLabels, TapComponent as TAP, TapGitHub
from modules.runner.tap_test_case import TapTestCase
from modules.markers import priority, components
from modules.service_tools.psql import PsqlTable, PsqlColumn, PsqlRow
from modules.tap_object_model import Application, ServiceInstance, ServiceType
from modules.test_names import generate_test_object_name


logged_components = (TAP.service_catalog,)
pytestmark = [components.service_catalog]


class Postgres(TapTestCase):

    psql_app = None
    test_table_name = "oh_hai"
    test_columns = [{"name": "col0", "type": "VARCHAR", "max_len": 15},
                    {"name": "col1", "type": "INTEGER", "is_nullable": False},
                    {"name": "col2", "type": "BOOLEAN", "is_nullable": True}]
    row_value_list = [[{"column_name": "col0", "value": "kitten"}, {"column_name": "col1", "value": 42},
                       {"column_name": "col2", "value": True}],
                      [{"column_name": "col1", "value": 0}],
                      [{"column_name": "col0", "value": None}, {"column_name": "col1", "value": 9000},
                       {"column_name": "col2", "value": None}]]

    @pytest.fixture(scope="class", autouse=True)
    def postgres_instance(self, request, test_org, test_space):
        self.step("Create postgres service instance")
        marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)
        psql = next(service for service in marketplace if service.label == ServiceLabels.PSQL)
        instance_name = generate_test_object_name()
        psql_instance = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.PSQL,
            name=instance_name,
            service_plan_guid=psql.service_plan_guids[0]
        )

        def fin():
            psql_instance.cleanup()
        request.addfinalizer(fin)
        return psql_instance

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def setup_psql_api_app(cls, request, test_space, login_to_cf, postgres_instance):
        cls.step("Get sql api app sources")
        sql_api_sources = app_sources.AppSources(repo_name=TapGitHub.sql_api_example, repo_owner=TapGitHub.intel_data,
                                                 gh_auth=config.CONFIG["github_auth"])
        psql_app_path = sql_api_sources.clone_or_pull()
        cls.step("Push psql api app to cf")
        cls.psql_app = Application.push(space_guid=test_space.guid, source_directory=psql_app_path,
                                        bound_services=(postgres_instance.name,),
                                        env_proxy=config.CONFIG["pushed_app_proxy"])

        def fin():
            cls.psql_app.cleanup()
        request.addfinalizer(fin)

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

    def _get_expected_rows(self):
        expected_rows = []
        for row_value in self.row_value_list:
            id = PsqlRow.post(self.psql_app, self.test_table_name, row_value)
            expected_rows.append(self._create_expected_row(self.psql_app, self.test_table_name, id, row_value))
        return expected_rows

    @priority.medium
    def test_create_and_delete_table(self):
        test_table = PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        table_list = PsqlTable.get_list(self.psql_app)
        self.assertIn(test_table, table_list)
        test_table.delete()
        table_list = PsqlTable.get_list(self.psql_app)
        self.assertNotIn(test_table, table_list)

    @priority.medium
    def test_get_table_columns(self):
        test_table = PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_columns = [PsqlColumn.from_json_definition(c) for c in self.test_columns]
        expected_columns.append(PsqlColumn("id", "INTEGER", False, None))
        columns = test_table.get_columns()
        self.assertEqual(len(columns), len(expected_columns))
        for column in expected_columns:
            self.assertIn(column, columns)

    @priority.medium
    def test_post_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        for row_id, row_values in list(enumerate(self.row_value_list)):
            with self.subTest(row=row_values):
                row_id += 1  # psql's 1-based indexing
                new_row_id = PsqlRow.post(self.psql_app, self.test_table_name, row_values)
                expected_row = self._create_expected_row(self.psql_app, self.test_table_name, new_row_id, row_values)
                row_list = PsqlRow.get_list(self.psql_app, self.test_table_name)
                self.assertIn(expected_row, row_list)
                row = PsqlRow.get(self.psql_app, self.test_table_name, row_id)
                self.assertEqual(row, expected_row)

    @priority.low
    def test_post_multiple_rows(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows()
        rows = PsqlRow.get_list(self.psql_app, self.test_table_name)
        self.assertListEqual(rows, expected_rows)

    @priority.medium
    def test_put_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows()
        new_values = [{"column_name": "col0", "value": "oh hai"}, {"column_name": "col2", "value": True}]
        expected_rows[1].put(new_values)
        row = PsqlRow.get(self.psql_app, self.test_table_name, row_id=expected_rows[1].id)
        self.assertEqual(expected_rows[1], row)

    @priority.medium
    def test_delete_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        posted_rows = self._get_expected_rows()
        posted_rows[1].delete()
        rows = PsqlRow.get_list(self.psql_app, self.test_table_name)
        self.assertNotIn(posted_rows[1], rows)
