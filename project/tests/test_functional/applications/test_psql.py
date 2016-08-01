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

import config
from modules.app_sources import AppSources
from modules.constants import ServiceLabels, TapComponent as TAP, TapGitHub
from modules.markers import priority, components
from modules.service_tools.psql import PsqlTable, PsqlColumn, PsqlRow
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, ServiceType
from modules.test_names import generate_test_object_name
from tests.fixtures.db_input import DbInput

logged_components = (TAP.service_catalog,)
pytestmark = [components.service_catalog]


class TestPsql(object):
    psql_app = None
    test_table_name = DbInput.test_table_name
    test_columns = DbInput.test_columns
    row_value_list = DbInput.test_rows_1

    @pytest.fixture(scope="class", autouse=True)
    def postgres_instance(self, class_context, test_org, test_space):
        step("Create postgres service instance")
        marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)
        psql = next(service for service in marketplace if service.label == ServiceLabels.PSQL)
        instance_name = generate_test_object_name()
        psql_instance = ServiceInstance.api_create(
            context=class_context,
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.PSQL,
            name=instance_name,
            service_plan_guid=psql.service_plan_guids[0]
        )
        return psql_instance

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def setup_psql_api_app(cls, test_space, login_to_cf, postgres_instance, class_context):
        step("Get sql api app sources")
        sql_api_sources = AppSources.from_github(
            repo_name=TapGitHub.sql_api_example,
            repo_owner=TapGitHub.intel_data,
            gh_auth=config.github_credentials()
        )
        step("Push psql api app to cf")
        cls.psql_app = Application.push(
            class_context,
            space_guid=test_space.guid, 
            source_directory=sql_api_sources.path,
            bound_services=(postgres_instance.name,)
        )

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
        self.__class__.test_table_name = generate_test_object_name(prefix=DbInput.test_table_name)
        test_table = PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        table_list = PsqlTable.get_list(self.psql_app)
        assert test_table in table_list
        test_table.delete()
        table_list = PsqlTable.get_list(self.psql_app)
        assert test_table not in table_list

    @priority.medium
    def test_get_table_columns(self):
        test_table = PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_columns = [PsqlColumn.from_json_definition(c) for c in self.test_columns]
        expected_columns.append(PsqlColumn("id", "INTEGER", False, None))
        columns = test_table.get_columns()
        assert len(columns) == len(expected_columns)
        for column in expected_columns:
            assert column in columns

    @priority.medium
    @pytest.mark.parametrize("row_values", row_value_list)
    def test_post_row(self, row_values):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        new_row_id = PsqlRow.post(self.psql_app, self.test_table_name, row_values)
        expected_row = self._create_expected_row(self.psql_app, self.test_table_name, new_row_id, row_values)
        row_list = PsqlRow.get_list(self.psql_app, self.test_table_name)
        assert expected_row in row_list
        row = PsqlRow.get(self.psql_app, self.test_table_name, row_id=1)
        assert row == expected_row

    @priority.low
    def test_post_multiple_rows(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows()
        rows = PsqlRow.get_list(self.psql_app, self.test_table_name)
        assert rows == expected_rows

    @priority.medium
    def test_put_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_rows = self._get_expected_rows()
        new_values = [{"column_name": "col0", "value": self.test_table_name}, {"column_name": "col2", "value": True}]
        expected_rows[1].put(new_values)
        row = PsqlRow.get(self.psql_app, self.test_table_name, row_id=expected_rows[1].id)
        assert expected_rows[1] == row

    @priority.medium
    def test_delete_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        posted_rows = self._get_expected_rows()
        posted_rows[1].delete()
        rows = PsqlRow.get_list(self.psql_app, self.test_table_name)
        assert posted_rows[1] not in rows
