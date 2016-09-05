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

import tests.test_components.test_app_deploy_start as tads
from modules import file_utils
from modules.constants import TapComponent as TAP, Urls
from modules.http_calls.platform.catalog import update_instance
from modules.markers import priority, incremental
from modules.tap_logger import step
from modules.tap_object_model.console_service import ConsoleService
from modules.tap_object_model.k8s_application import K8sApplication
from modules.test_names import generate_test_object_name

logged_components = (TAP.api_service, TAP.catalog)
pytestmark = [pytest.mark.components(TAP.api_service, TAP.catalog)]


@incremental
@priority.medium
@pytest.mark.usefixtures("open_tunnel")
class TestCodePackagingAndAppPushing:
    MANIFEST_NAME = "manifest.json"
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    APP_NAME = generate_test_object_name(prefix="samplepythonapp").replace('_', '')
    file_utils.TMP_FILE_DIR = "{}{}".format(file_utils.TMP_FILE_DIR, generate_test_object_name(prefix="/"))
    SAMPLE_APP_URL = Urls.tapng_python_app_url

    @pytest.fixture(scope="class")
    def python_app_path(self):
        self.__class__.application_file_path = file_utils.download_file(self.SAMPLE_APP_URL, self.SAMPLE_APP_TAR_NAME)
        return self.application_file_path

    @pytest.fixture(scope="class")
    def manifest_path(self):
        self.__class__.manifest_file_path = file_utils.download_file(Urls.manifest_url, self.MANIFEST_NAME)
        return self.manifest_file_path

    def test_0_push_application(self, class_context, python_app_path, manifest_path):
        step("Change manifest.json params")
        manifest_params = {
            'instances': 1,
            'name': self.APP_NAME,
            'type': "PYTHON"
        }
        tads.TestPythonApplicationFlow.change_json_file_param_value(file_path=self.manifest_file_path,
                                                                    manifest_params=manifest_params)
        step("Push application")
        self.__class__.app = K8sApplication.push(class_context, python_app_path, manifest_path)
        step("Ensure application is running")
        self.app.ensure_running()
        step("Get application")
        app = K8sApplication.get(app_id=self.app.id)
        step("Check application parameters")
        assert app.name == self.APP_NAME, "Application has inproper name"
        assert app.state == K8sApplication.STATE_RUNNING, "Application is not running"
        assert app.replication is 1, "Application replication is incorrect"
        assert app.image_state == "READY", "Application image state is incorrect"

    def test_1_change_app_state_and_remove_it(self):
        step("Update app state")
        update_instance(instance_id=self.app.id, field="state", value=K8sApplication.STATE_FAILURE)
        step("Check app state")
        app = K8sApplication.get(app_id=self.app.id)
        assert app.state == K8sApplication.STATE_FAILURE, "Application is not in {} state".format(
            K8sApplication.STATE_FAILURE)
        step("Delete app")
        self.app.delete()
        step("Check if app is removed")
        apps = ConsoleService.get_applications()
        assert self.APP_NAME not in apps.content.decode()
        step("Remove downloaded files")
        file_utils.tear_down_test_files()
