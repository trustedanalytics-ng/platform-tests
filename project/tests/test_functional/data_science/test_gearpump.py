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
from modules.constants import TapComponent as TAP, Urls, ServicePlan
from modules.markers import components, priority
from modules.service_tools.gearpump import Gearpump
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance

logged_components = (TAP.gearpump_broker, TAP.application_broker, TAP.service_catalog)
pytestmark = [components.gearpump_broker, components.application_broker, components.service_catalog]


class TestGearpumpConsole(object):

    COMPLEXDAG_APP_NAME = "dag"
    ONE_WORKER_PLAN_NAME = ServicePlan.WORKER_1
    COMPLEXDAG_FILE_NAME = Urls.complexdag_app_url.split("/")[-1]

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def download_complexdag(cls):
        step("Download file complexdag")
        cls.complexdag_app_path = download_file(
            url=Urls.complexdag_app_url,
            save_file_name=cls.COMPLEXDAG_FILE_NAME
        )

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def create_gearpump(cls, test_org, test_space):
        step("Create gearpump instance with plan: 1 worker")
        cls.gearpump = Gearpump(test_org.guid, test_space.guid, service_plan_name=cls.ONE_WORKER_PLAN_NAME)
        step("Check that gearpump instance has been created")
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        if cls.gearpump.instance not in instances:
            raise AssertionError("gearpump instance is not on list of instances")
        cls.gearpump.get_credentials()
        step("Log into gearpump UI")
        cls.gearpump.login()

    @priority.high
    def test_submit_complexdag_app_to_gearpump_dashboard(self):
        step("Submit application complexdag to gearpump dashboard")
        dag_app = self.gearpump.submit_application_jar(self.complexdag_app_path, self.COMPLEXDAG_APP_NAME)
        step("Check that submitted application is started")
        assert dag_app.is_started is True
        step("Kill application")
        dag_app.kill_application()
        step("Check that killed application is stopped")
        assert dag_app.is_started is False
