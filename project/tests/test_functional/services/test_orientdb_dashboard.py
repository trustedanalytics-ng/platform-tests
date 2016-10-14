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

from modules.application_stack_validator import ApplicationStackValidator
from modules.constants import ApplicationPath, ServiceLabels
from modules.markers import priority, incremental
from modules.service_tools.orientdb_api import OrientDbApi
from modules.service_tools.orientdb_dashboard_api import OrientDbDashboardApi
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance, ServiceOffering


@pytest.mark.skip("DPNG-8773 [api-tests] Adjust test_orientdb tests to TAP NG")
@incremental
@priority.low
class TestOrientdbDashboard:

    ORIENTDB_DASHBOARD_APP_NAME = "orientdb-dashboard"

    def test_0_validate_core_orientdb_dashboard_app_and_service(self, core_space):
        step("Validate orientdb dashboard app in core space")
        self.__class__.orientdb_instance = next((s for s in ServiceInstance.api_get_list(core_space.guid)
                                                 if s.service_label == ServiceLabels.ORIENT_DB and
                                                 s.bound_apps[0]["app_name"] == self.ORIENTDB_DASHBOARD_APP_NAME), None)
        validator = ApplicationStackValidator(self.orientdb_instance)
        validator.validate(expected_bindings=[ServiceLabels.ORIENT_DB])
        self.__class__.orientdb_dashboard_app = validator.application

    def test_1_check_orientdb_dashboard_service_is_available_in_marketplace(self, core_space):
        step("Check if orientdb dashboard service is in marketplace")
        marketplace = ServiceOffering.get_list()
        orientdb_dashboard_service = next((service for service in marketplace
                                           if service.label == ServiceLabels.ORIENT_DB_DASHBOARD), None)
        assert orientdb_dashboard_service is not None, "OrientDB service not available in marketplace"

    def test_2_add_and_delete_key_to_orientdb_service_instance(self, core_space):
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

    def test_3_push_test_orientdb_api_app(self, class_context, core_space, login_to_cf_core):
        step("Push orientdb-api application to cf")
        self.__class__.orientdb_api_app = Application.push(context=class_context,
                                                           source_directory=ApplicationPath.ORIENTDB_API,
                                                           space_guid=core_space.guid,
                                                           bound_services=(self.orientdb_instance.name,))
        step("Check orientdb-api application has url")
        assert len(self.orientdb_api_app.urls) == 1
        step("Check the orientdb-api application is running")
        self.orientdb_api_app.ensure_started()

    def test_4_create_database_in_orientdb(self):
        step("Create and check database in orientdb")
        self.__class__.orientdb_api = OrientDbApi(app=self.orientdb_api_app)
        self.__class__.database_name = self.orientdb_api.database_create()
        assert self.database_name is not None, "Database was not created"
        response = self.orientdb_api.database_get()
        assert len(response) == 1

    def test_5_create_class_and_record_in_orientdb(self):
        step("Create and check class in database in orientdb")
        self.__class__.class_name = self.orientdb_api.class_create()
        assert self.class_name is not None, "Class was not created"
        step("Create and check record in database in orientdb")
        self.orientdb_api.record_create()
        response = self.orientdb_api.record_get_all()
        assert len(response["Records"]) == 1

    def test_6_check_orientdb_dashboard_app(self):
        step("Create OrientDB dashboard application API")
        self.__class__.orientdb_dashboard_api = OrientDbDashboardApi(orientdb_api_app=self.orientdb_api_app,
                                                                     orientdb_dashboard_app=self.orientdb_dashboard_app)
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
        expected_record = self.orientdb_api.record()
        assert result["@class"] == self.class_name
        assert all(key in result for key in expected_record)
        assert all(result[key] == value for key, value in expected_record.items() if key != "id")

    def test_7_drop_database(self):
        step("Delete database")
        self.orientdb_api.database_delete()
        step("Check database does not exist")
        database_list = self.orientdb_dashboard_api.get_database_names()
        assert self.database_name not in database_list
