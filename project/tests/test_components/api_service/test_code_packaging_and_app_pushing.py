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

from modules.constants import TapComponent as TAP, Urls, TapApplicationType, TapEntityState
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority, incremental
from modules.tap_logger import step
from modules.tap_object_model.application import Application
from modules.test_names import generate_test_object_name

logged_components = (TAP.api_service, TAP.catalog)
pytestmark = [pytest.mark.components(TAP.api_service, TAP.catalog)]


@incremental
@priority.medium
@pytest.mark.usefixtures("open_tunnel")
@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
@pytest.mark.bugs("DPNG-11677 Not possible to push PYTHON2.7 or PYTHON3.4 apps")
class TestCodePackagingAndAppPushing:
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    APP_NAME = generate_test_object_name(prefix="samplepythonapp").replace('_', '')
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    MANIFEST_PARAMS = {
        'instances': 1,
        'name': APP_NAME,
        'type': TapApplicationType.PYTHON27
    }

    @pytest.mark.bugs("DPNG-8751 Adjust sample-python-app to TAP NG")
    def test_0_push_application(self, class_context, sample_app_path, sample_manifest_path, tap_cli):
        step("Change manifest.json params")
        Application.update_manifest(sample_manifest_path, self.MANIFEST_PARAMS)
        step("Push application")
        self.__class__.app = Application.push(class_context, app_dir=sample_app_path, tap_cli=tap_cli)
        step("Ensure application is running")
        self.app.ensure_running()
        step("Get application")
        app = Application.get(app_id=self.app.id)
        step("Check application parameters")
        assert app.name == self.APP_NAME, "Application has incorrect name"
        assert app.state == TapEntityState.RUNNING, "Application is not running"
        assert app.replication is 1, "Application replication is incorrect"
        assert app.image_state == TapEntityState.READY, "Application image state is incorrect"

    def test_1_change_app_state_and_remove_it(self):
        step("Update app state")
        catalog_api.update_instance(instance_id=self.app.id, field_name="state", value=TapEntityState.FAILURE)
        step("Check app state")
        app = Application.get(app_id=self.app.id)
        assert app.state == TapEntityState.FAILURE, "Application is not in the expected state"
        step("Delete app")
        self.app.delete()
        step("Check if app is removed")
        apps = Application.get_list()
        assert self.app not in apps
