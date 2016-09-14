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

from modules import file_utils
from modules.constants import TapComponent as TAP, Urls
from modules.http_calls.platform.catalog import update_instance
from modules.markers import priority, incremental
from modules.tap_logger import step
from modules.tap_object_model.k8s_application import K8sApplication
from modules.test_names import generate_test_object_name

logged_components = (TAP.api_service, TAP.catalog)
pytestmark = [pytest.mark.components(TAP.api_service, TAP.catalog)]


@incremental
@priority.medium
@pytest.mark.usefixtures("open_tunnel")
class TestCodePackagingAndAppPushing:
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    APP_NAME = generate_test_object_name(prefix="samplepythonapp").replace('_', '')
    file_utils.TMP_FILE_DIR = "{}{}".format(file_utils.TMP_FILE_DIR, generate_test_object_name(prefix="/"))
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    MANIFEST_PARAMS = {
        'instances': 1,
        'name': APP_NAME,
        'type': "PYTHON"
    }

    def test_0_push_application(self, class_context, sample_app_path, sample_manifest_path):
        step("Change manifest.json params")
        K8sApplication.update_manifest(sample_manifest_path, self.MANIFEST_PARAMS)
        step("Push application")
        self.__class__.app = K8sApplication.push(class_context, sample_app_path, sample_manifest_path)
        step("Ensure application is running")
        self.app.ensure_running()
        step("Get application")
        app = K8sApplication.get(self.app.id)
        step("Check application parameters")
        assert app.name == self.APP_NAME, "Application has incorrect name"
        assert app.state == K8sApplication.STATE_RUNNING, "Application is not running"
        assert app.replication is 1, "Application replication is incorrect"
        assert app.image_state == "READY", "Application image state is incorrect"

    def test_1_change_app_state_and_remove_it(self):
        step("Update app state")
        update_instance(instance_id=self.app.id, field="state", value=K8sApplication.STATE_FAILURE)
        step("Check app state")
        app = K8sApplication.get(self.app.id)
        assert app.state == K8sApplication.STATE_FAILURE, "Application is not in the expected state"
        step("Delete app")
        self.app.delete()
        step("Check if app is removed")
        apps = K8sApplication.get_list()
        assert self.app not in apps
