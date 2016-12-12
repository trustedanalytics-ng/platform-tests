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

from modules.constants import TapApplicationType, TapComponent as TAP, Urls
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Application
from modules.tap_object_model.prep_app import PrepApp
from tests.fixtures import assertions


logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]


@pytest.mark.usefixtures("open_tunnel")
class ApiServiceApplicationFlow:

    @pytest.fixture(scope="class")
    def sample_application(self, class_context, sample_app_path, api_service_admin_client):
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(sample_app_path)
        manifest_params = {"type": self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        log_fixture("Push sample application and check it's running")
        application = Application.push(class_context, app_path=sample_app_path,
                                       name=p_a.app_name, manifest_path=manifest_path,
                                       client=api_service_admin_client)
        application.ensure_running()
        return application

    @pytest.mark.bugs("DPNG-11421 All cli commands have repeated http:// underneath and return ERROR")
    @priority.high
    def test_push_and_delete_application(self, context, sample_app_path, api_service_admin_client):
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(sample_app_path)
        manifest_params = {"type": self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push sample application")
        application = Application.push(context, app_path=sample_app_path,
                                       name=p_a.app_name, manifest_path=manifest_path,
                                       client=api_service_admin_client)
        step("Check application is running")
        application.ensure_running()
        step("Stop application")
        application.stop()
        application.ensure_stopped()
        step("Delete application")
        application.delete()
        step("Check that application is not on the list")
        assertions.assert_not_in_with_retry(application, Application.get_list, client=api_service_admin_client)

    @priority.high
    def test_stop_and_start_application(self, sample_application):
        step("Stop application")
        sample_application.stop()
        step("Check that the application is stopped")
        sample_application.ensure_stopped()
        step("Start application")
        sample_application.start()
        step("Check application is ready")
        sample_application.ensure_running()

    @priority.medium
    def test_get_application_logs(self, sample_application, api_service_admin_client):
        step("Check that getting application logs returns no error")
        response = sample_application.get_logs(client=api_service_admin_client)
        # TODO assert something more meaningful
        assert type(response) is dict

    @priority.medium
    def test_scale_application(self, sample_application, api_service_admin_client):
        step("Scale application")
        replicas_number = 3
        response = sample_application.scale(replicas=replicas_number, client=api_service_admin_client)
        step("Check number of application instances")
        app_info = Application.get(sample_application.id, client=api_service_admin_client)
        assert app_info.running_instances == replicas_number


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
@pytest.mark.bugs("DPNG-11677 Not possible to push PYTHON2.7 or PYTHON3.4 apps")
class TestPythonApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    APP_TYPE = TapApplicationType.PYTHON27


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestNodeJsApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP_URL = Urls.tapng_nodejs_app_url
    APP_TYPE = TapApplicationType.NODEJS


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestGoApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP_URL = Urls.tapng_go_app_url
    APP_TYPE = TapApplicationType.GO


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestJavaApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP_URL = Urls.tapng_java_app_url
    APP_TYPE = TapApplicationType.JAVA
