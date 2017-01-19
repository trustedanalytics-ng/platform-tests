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

from modules.constants import ServicePlan, TapComponent as TAP
from modules.markers import incremental
from modules.service_tools.gearpump import Gearpump
from modules.tap_logger import step
from modules.yarn import YarnAppStatus


logged_components = (TAP.gearpump_broker, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.gearpump_broker, TAP.service_catalog)]


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestGearpumpConsole:

    COMPLEXDAG_APP_NAME = "dag"
    PLAN_NAME = ServicePlan.SMALL

    gearpump = None
    dag_app = None

    @pytest.fixture(scope="function")
    def go_to_dashboard(self):
        self.gearpump.go_to_dashboard()

    def test_0_create_gearpump_instance(self, class_context, test_org):
        """
        <b>Description:</b>
        Checks if creating gearpump instance with given PLAN_ID works.

        <b>Input data:</b>
        1. Plan name.
        2. Instance name.

        <b>Expected results:</b>
        Test passes when newly created instance is RUNNING and YARN application is also RUNNING.

        <b>Steps:</b>
        1. Create gearpump instance.
        2. Verify that HTTP response status code is 200 and instance status is RUNNING.
        3. Verify that YARN application status is RUNNING.
        """
        step("Create gearpump instance with plan {} ".format(self.PLAN_NAME))
        self.__class__.gearpump = Gearpump(class_context, service_plan_name=self.PLAN_NAME)
        step("Ensure that instance is running")
        self.gearpump.instance.ensure_running()
        step("Check yarn app status")
        yarn_app_status = self.gearpump.get_yarn_app_status()
        assert yarn_app_status == YarnAppStatus.RUNNING

    @pytest.mark.bugs("DPNG-15154 Gearpump dashboard url doesn't work")
    def test_1_check_gearpump_ui_app_created(self):
        """
        <b>Description:</b>
        Checks if gearpumpdashboard instance is automatically created during creating gearpump instance.

        <b>Input data:</b>
        1. Gearpump instance.

        <b>Expected results:</b>
        Test passes when gearpumpdashboard instance was successfully created.

        <b>Steps:</b>
        1. Check if gearpumpdashboard instance was automatically created.
        2. Get gearpump credentials.
        """
        step("Check that gearpump ui app has been created")
        gearpump_ui_app = self.gearpump.get_ui_app()
        assert gearpump_ui_app is not None, "Gearpump ui application was not created"
        self.gearpump.get_credentials()

    def test_2_submit_complexdag_app_to_gearpump_dashboard(self, go_to_dashboard, test_data_urls):
        """
        <b>Description:</b>
        Checks if submitted Application is RUNNING on gearpump dashboard.

        <b>Input data:</b>
        1. Complexdag sample application(jar file)

        <b>Expected results:</b>
        Test passes when submitted Application is RUNNING on gearpump dashboard.

        <b>Steps:</b>
        1. Verify that application is submitted on gearpump dashboard.
        2. Check if submitted application is RUNNING.
        """
        step("Submit application complexdag to gearpump dashboard")
        self.__class__.dag_app = self.gearpump.get_gearpump_application(test_data_urls.complexdag_app.filepath,
                                                                        self.COMPLEXDAG_APP_NAME)
        step("Check that submitted application is started")
        assert self.dag_app.is_started

    def test_3_kill_complexdag_app(self, go_to_dashboard):
        """
        <b>Description:</b>
        Checks if Gearpump application can be STOPPED.

        <b>Input data:</b>
        1. Gearpump application.

        <b>Expected results:</b>
        Test passes when application is STOPPED.

        <b>Steps:</b>
        1. Send DELETE request with application id.
        2. Check that application is STOPPED.
        """
        step("Kill application")
        self.dag_app.kill_application()
        step("Check that application is stopped")
        assert not self.dag_app.is_started

    @pytest.mark.bugs("DPNG-15071 Gearpump service removal issue")
    def test_4_delete_gearpump_instance(self):
        """
        <b>Description:</b>
        Checks if Gearpump instance can be DELETED.

        <b>Input data:</b>
        1. Gearpump instance.

        <b>Expected results:</b>
        Test passes when instance is DELETED and Yarn application status is KILLED.

        <b>Steps:</b>
        1. Send the stop command to service instance.
        2. Check if instance is STOPPED (status == STOPPED)
        3. Send DELETE request with service id.
        4. Check if application disappeared from instance list.
        5. Verify that yarn application status is KILLED.
        """
        step("Stop service instance")
        self.gearpump.instance.stop()
        self.gearpump.instance.ensure_stopped()
        step("Delete gearpump instance")
        self.gearpump.instance.delete()
        step("Ensure that instance is running")
        self.gearpump.instance.ensure_deleted()
        step("Check yarn app status")
        yarn_app_status = self.gearpump.get_yarn_app_status()
        assert yarn_app_status == YarnAppStatus.KILLED

    def test_5_check_gearpump_ui_app_is_deleted(self):
        """
        <b>Description:</b>
        Checks if gearpumpdashboard instance is automatically deleted during removing gearpump instance.

        <b>Input data:</b>
        1. Gearpump instance.

        <b>Expected results:</b>
        Test passes when gearpumpdashboard instance was successfully deleted.

        <b>Steps:</b>
        1. Verify that gearpump ui application disappeared from instance list.
        """
        step("Check that gearpump ui application is deleted")
        gearpump_ui_app = self.gearpump.get_ui_app()
        assert gearpump_ui_app is None, "Gearpump ui app was not deleted"
