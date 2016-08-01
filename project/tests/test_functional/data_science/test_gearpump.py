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

from modules.file_utils import download_file
from modules.constants import ServicePlan, TapComponent as TAP, Urls
from modules.markers import incremental
from modules.service_tools.gearpump import Gearpump
from modules.tap_object_model import ServiceInstance
from modules.tap_logger import step
from modules.yarn import YarnAppStatus
from tests.fixtures import assertions

logged_components = (TAP.gearpump_broker, TAP.application_broker, TAP.service_catalog)
pytestmark = [pytest.mark.components(TAP.gearpump_broker, TAP.application_broker, TAP.service_catalog)]


@incremental
class TestGearpumpConsole:

    COMPLEXDAG_APP_NAME = "dag"
    ONE_WORKER_PLAN_NAME = ServicePlan.WORKER_1
    COMPLEXDAG_FILE_NAME = Urls.complexdag_app_url.split("/")[-1]

    gearpump = None
    dag_app = None

    @classmethod
    @pytest.fixture(scope="class")
    def complexdag_app_path(cls):
        step("Download file complexdag")
        return download_file(url=Urls.complexdag_app_url, save_file_name=cls.COMPLEXDAG_FILE_NAME)

    @pytest.fixture(scope="function")
    def go_to_dashboard(self, request):
        self.gearpump.go_to_dashboard()
        request.addfinalizer(self.gearpump.go_to_console)

    def test_0_create_gearpump_instance(self, class_context, test_org, test_space):
        step("Create gearpump instance with plan: 1 worker")
        self.__class__.gearpump = Gearpump(class_context, test_org.guid, test_space.guid,
                                           service_plan_name=self.ONE_WORKER_PLAN_NAME)
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        assert self.gearpump.instance in instances, "Gearpump instance is not on list of instances"
        step("Check yarn app status")
        yarn_app_status = self.gearpump.get_yarn_app_status()
        assert yarn_app_status == YarnAppStatus.RUNNING

    def test_1_check_gearpump_ui_app_created(self):
        step("Check that gearpump ui app has been created")
        gearpump_ui_app = self.gearpump.get_ui_app()
        assert gearpump_ui_app is not None, "Gearpump ui application was not created"
        self.gearpump.get_credentials()

    def test_2_submit_complexdag_app_to_gearpump_dashboard(self, add_admin_to_test_org, go_to_dashboard,
                                                           complexdag_app_path):
        step("Submit application complexdag to gearpump dashboard")
        self.__class__.dag_app = self.gearpump.submit_application_jar(complexdag_app_path, self.COMPLEXDAG_APP_NAME)
        step("Check that submitted application is started")
        assert self.dag_app.is_started

    def test_3_kill_complexdag_app(self, go_to_dashboard):
        step("Kill application")
        self.dag_app.kill_application()
        step("Check that application is stopped")
        assert not self.dag_app.is_started

    def test_4_delete_gearpump_instance(self, test_space):
        step("Delete gearpump instance")
        self.gearpump.instance.api_delete()
        assertions.assert_not_in_with_retry(self.gearpump.instance, ServiceInstance.api_get_list,
                                            space_guid=test_space.guid)
        step("Check yarn app status")
        yarn_app_status = self.gearpump.get_yarn_app_status()
        assert yarn_app_status == YarnAppStatus.KILLED

    def test_5_check_gearpump_ui_app_is_deleted(self):
        step("Check that gearpump ui application is deleted")
        gearpump_ui_app = self.gearpump.get_ui_app()
        assert gearpump_ui_app is None, "Gearpump ui app was not deleted"
