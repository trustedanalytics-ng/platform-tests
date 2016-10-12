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

from modules.constants import ApiServiceHttpStatus, TapApplicationType, TapComponent as TAP, Urls
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Application
from tests.fixtures import assertions


logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]


@pytest.mark.usefixtures("open_tunnel")
class ApiServiceApplicationFlow:

    @pytest.fixture(scope="class")
    def sample_application(self, class_context, sample_app_path, tap_cli):
        log_fixture("Push sample application and check it's running")
        application = Application.push(class_context, app_path=sample_app_path, tap_cli=tap_cli, app_type=self.APP_TYPE)
        application.ensure_running()
        return application

    @pytest.mark.bugs("DPNG-11421 All cli commands have repeated http:// underneath and return ERROR")
    def test_push_and_delete_application(self, context, sample_app_path, tap_cli):
        step("Push sample application")
        application = Application.push(context, app_path=sample_app_path, tap_cli=tap_cli, app_type=self.APP_TYPE)
        step("Check application is running")
        application.ensure_running()
        step("Delete application")
        application.delete()
        step("Check that application is not on the list")
        assertions.assert_not_in_with_retry(application, Application.get_list)

    def test_stop_and_start_application(self, sample_application):
        step("Stop application")
        sample_application.stop()
        step("Check that the application is stopped")
        sample_application.ensure_stopped()
        step("Start application")
        sample_application.start()
        step("Check application is ready")
        sample_application.ensure_running()

    @pytest.mark.skip("DPNG-11693: Checking logs in applications don't work yet")
    def test_get_application_logs(self, sample_application):
        step("Check that getting application logs returns no error")
        response = sample_application.get_logs()
        # TODO assert something more meaningful
        assert response.status_code == ApiServiceHttpStatus.CODE_OK

    @pytest.mark.skip("DPNG-11694: Scaling applications don't work yet")
    def test_scale_application(self, sample_application):
        step("Scale application")
        replicas_number = 3
        sample_application.scale(replicas_number)
        step("Check number of application instances")
        app_pods = sample_application.get_pods()
        assert len(app_pods) == replicas_number


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