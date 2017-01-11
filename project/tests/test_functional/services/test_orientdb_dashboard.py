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

from modules.constants import ApplicationPath, ServiceLabels
from modules.markers import priority, incremental
from modules.service_tools.orientdb_api import OrientDbApi
from modules.service_tools.orientdb_dashboard_api import OrientDbDashboardApi
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, ServiceOffering


@incremental
@priority.low
class TestOrientdbDashboard:

    @classmethod
    @pytest.fixture(scope="class")
    def orientdb_api(cls, app_bound_orientdb):
        return OrientDbApi(app_bound_orientdb)


    def test_0_add_and_delete_key_to_orientdb_service_instance(self):
        # This functionality changed in new TAP
        # step("Create a key for the orientdb instance")
        # orientdb_instance_key = ServiceKey.api_create(self.orientdb_instance.guid)
        # step("Check a key for the orientdb instance")
        # summary = ServiceInstance.api_get_keys(core_space.guid)
        # assert orientdb_instance_key in summary[self.orientdb_instance]
        # step("Delete orientdb service key")
        # orientdb_instance_key.api_delete()
        # step("Check that key has been deleted")
        # summary = ServiceInstance.api_get_keys(core_space.guid)
        # assert orientdb_instance_key not in summary[self.orientdb_instance]
        pass

    def test_1_create_database_in_orientdb(self, orientdb_api):
        """
        <b>Description:</b>
        Check that it's possible to create database in orientdb.

        <b>Input data:</b>
        1. orientdb api application

        <b>Expected results:</b>
        Test passes if database was created.

        <b>Steps:</b>
        1. Create database.
        2. Check that database was created.
        """
        step("Create and check database in orientdb")
        self.__class__.database_name = orientdb_api.database_create()
        assert self.database_name is not None, "Database was not created"
        response = orientdb_api.database_get()
        assert len(response) == 1

    def test_2_create_class_and_record_in_orientdb(self, orientdb_api):
        """
        <b>Description:</b>
        Check that it's possible to create class and add record to orientdb.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if class and record are created.

        <b>Steps:</b>
        1. Create class in orientdb.
        2. Check that class was created.
        3. Create record in orientdb.
        4. Check that record was added.
        """
        step("Create and check class in database in orientdb")
        self.__class__.class_name = orientdb_api.class_create()
        assert self.class_name is not None, "Class was not created"
        step("Create and check record in database in orientdb")
        orientdb_api.record_create()
        response = orientdb_api.record_get_all()
        assert len(response["Records"]) == 1

    def test_3_check_orientdb_dashboard_app(self, orientdb_api, orientdb_instance):
        """
        <b>Description:</b>
        Check orientdb dashboard app.

        <b>Input data:</b>
        1. tested database name

        <b>Expected results:</b>
        Test passes if all orientdb dashboard application functionalities work properly.

        <b>Steps:</b>
        1. Retrieve database names using application.
        2. Check that database name is in retrieved list.
        3. Get database information using application.
        4. Check that retrieved informations contain class name.
        5. Get user roles using app.
        6. Check that all retrieved roles are 'ACTIVE'.
        7. Get records from class and compare them with expected records.
        """
        # orientdb_dashboard is the same as orientdb_instance, but contains more data (url)
        orientdb_dashboard = next((s for s in ServiceInstance.get_list()
                                   if s.offering_label == ServiceLabels.ORIENT_DB
                                   if s.name == orientdb_instance.name),
                                  None)
        step("Create OrientDB dashboard application API")
        self.__class__.orientdb_dashboard_api = OrientDbDashboardApi(orientdb_api_app=orientdb_api,
                                                                     orientdb_dashboard_app=orientdb_dashboard)
        step("Check database exists")
        assert self.database_name in self.orientdb_dashboard_api.get_database_names()
        step("Check database info")
        database_info = self.orientdb_dashboard_api.get_database_info(database_name=self.database_name)
        assert self.class_name in [i["name"] for i in database_info["classes"]]
        step("Check user roles")
        roles = self.orientdb_dashboard_api.get_user_roles(database_name=self.database_name)
        assert all(r == "ACTIVE" for r in roles.values())
        step("Execute command select from class")
        result = self.orientdb_dashboard_api.select_from_class(database_name=self.database_name,
                                                               class_name=self.class_name)[0]
        expected_record = orientdb_api.record()
        assert result["@class"] == self.class_name
        assert all(key in result for key in expected_record)
        assert all(result[key] == value for key, value in expected_record.items() if key != "id")

    def test_4_drop_database(self, orientdb_api):
        """
        <b>Description:</b>
        Check that database can be deleted.

        <b>Input data:</b>
        No input data.

        <b>Expected results:</b>
        Test passes if database is successfully deleted.

        <b>Steps:</b>
        1. Delete database.
        2. Check that database was deleted.
        """
        step("Delete database")
        orientdb_api.database_delete()
        step("Check database does not exist")
        database_list = self.orientdb_dashboard_api.get_database_names()
        assert self.database_name not in database_list
