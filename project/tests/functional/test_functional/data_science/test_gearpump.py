#
# Copyright (c) 2016 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from modules.file_utils import download_file
from modules.constants import TapComponent as TAP, Urls
from modules.remote_logger.remote_logger_decorator import log_components
from modules.runner.tap_test_case import TapTestCase
from modules.runner.decorators import components, priority
from modules.service_tools.gearpump import Gearpump
from modules.tap_object_model import Organization, ServiceInstance, Space
from tests.fixtures import teardown_fixtures


@log_components()
@components(TAP.gearpump_broker, TAP.application_broker, TAP.service_catalog)
class GearpumpConsole(TapTestCase):
    COMPLEXDAG_APP_NAME = "dag"
    ONE_WORKER_PLAN_NAME = "1 worker"
    COMPLEXDAG_FILE_NAME = Urls.complexdag_app_url.split("/")[-1]

    @classmethod
    @teardown_fixtures.cleanup_after_failed_setup
    def setUpClass(cls):
        cls.step("Download file complexdag")
        cls.complexdag_app_path = download_file(url=Urls.complexdag_app_url, save_file_name=cls.COMPLEXDAG_FILE_NAME)
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create()
        cls.test_space = Space.api_create(cls.test_org)
        cls.step("Create gearpump instance with plan: 1 worker")
        cls.gearpump = Gearpump(cls.test_org.guid, cls.test_space.guid, service_plan_name=cls.ONE_WORKER_PLAN_NAME)
        cls._assert_gearpump_instance_created(gearpump_data_science=cls.gearpump.data_science,
                                              space_guid=cls.test_space.guid)
        cls.step("Log into gearpump UI")
        cls.gearpump.login()

    @classmethod
    def _assert_gearpump_instance_created(cls, gearpump_data_science, space_guid):
        cls.step("Check that gearpump instance has been created")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        if gearpump_data_science.instance not in instances:
            raise AssertionError("gearpump instance is not on list of instances")
        gearpump_data_science.get_credentials()

    @priority.high
    def test_submit_complexdag_app_to_gearpump_dashboard(self):
        self.step("Submit application complexdag to gearpump dashboard")
        dag_app = self.gearpump.submit_application_jar(self.complexdag_app_path, self.COMPLEXDAG_APP_NAME)
        self.step("Check that submitted application is started")
        self.assertTrue(dag_app.is_started)
        self.step("Kill application")
        dag_app.kill_application()
        self.step("Check that killed application is stopped")
        self.assertFalse(dag_app.is_started)
