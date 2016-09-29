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

from modules.constants import ApiServiceHttpStatus
from modules.constants import TapComponent as TAP
from modules.constants.urls import Urls
from modules.markers import incremental
from modules.tap_logger import step
from modules.tap_object_model.api_service import ApiService
from modules.tap_object_model.k8s_application import K8sApplication
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestPythonApplicationFlow:
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    APP_NAME = "samplepythonapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "PYTHON"

    @property
    def manifest_params(self):
        return {
            'instances': 1,
            'name': self.APP_NAME,
            'type': self.APP_TYPE
        }

    @pytest.mark.bugs("DPNG-10722 sample-java-app from platform-tests does not work on new tap")
    @pytest.mark.bugs("DPNG-11421 All cli commands have repeated http:// underneath and return ERROR"
    def test_0_push_application(self, class_context, sample_app_path, sample_manifest_path):
        step("Prepare manifest with parameters")
        K8sApplication.update_manifest(sample_manifest_path, self.manifest_params)
        step("Push sample application")
        self.__class__.application = K8sApplication.push(class_context, sample_app_path, sample_manifest_path)
        step("Check application is running")
        self.application.ensure_running()
        step("Check application is ready")
        self.application.ensure_ready()

    def test_1_stop_application(self):
        step("Stop application")
        self.application.stop()
        step("Check that the application is stopped")
        self.application.ensure_stopped()
        self.application.ensure_is_down()

    def test_2_start_application(self):
        step("Start application")
        self.application.start()
        step("Check application is ready")
        self.application.ensure_ready()

    def test_3_check_logs(self):
        step("Check that getting application logs returns no error")
        response = self.application.get_logs()
        assert response.status_code == ApiServiceHttpStatus.CODE_OK

    def test_4_scale_application(self):
        step("Scale application")
        replicas_number = 3
        self.application.scale(replicas_number)
        step("Check number of application instances")
        app_pods = self.application.get_pods()
        assert len(app_pods) == replicas_number

    def test_5_delete_application(self):
        step("Delete application")
        self.application.delete()
        step("Check that application url is unavailable")
        self.application.ensure_is_down()


@incremental
class TestNodeJsApplicationFlow(TestPythonApplicationFlow):
    SAMPLE_APP_URL = Urls.tapng_nodejs_app_url
    APP_NAME = "samplenodejsapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "NODEJS"


@incremental
class TestGoApplicationFlow(TestPythonApplicationFlow):
    SAMPLE_APP_URL = Urls.tapng_go_app_url
    APP_NAME = "samplegoapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "GO"


@incremental
class TestJavaApplicationFlow(TestPythonApplicationFlow):
    SAMPLE_APP_URL = Urls.tapng_java_app_url
    APP_NAME = "samplejavaapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "JAVA"


class TestSampleApp:
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    APP_NAME = "sampleapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "PYTHON"

    MANIFEST_PARAMS = {
        'instances': 1,
        'name': APP_NAME,
        'type': APP_TYPE
    }

    @pytest.fixture(scope="class", autouse=True)
    def sample_app(self, class_context, sample_app_path, sample_manifest_path):
        step("Prepare manifest with parameters")
        K8sApplication.update_manifest(sample_manifest_path, self.MANIFEST_PARAMS)
        step("Push sample application")
        application = K8sApplication.push(class_context, sample_app_path, sample_manifest_path)
        step("Check application is running")
        application.ensure_running()
        step("Check application is ready")
        application.ensure_ready()

    @pytest.mark.bugs("DPNG-11054 [TAP_NG] Response code 409 (name conflict) should be displayed when pushing twice app with the same name")
    def test_cannot_push_application_twice(self, class_context, sample_app_path, sample_manifest_path):
        step("Check that pushing the same application again causes an error")
        K8sApplication.update_manifest(sample_manifest_path, self.MANIFEST_PARAMS)
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_CONFLICT, "",
                                     K8sApplication.push, class_context, sample_app_path, sample_manifest_path)

    def test_cannot_scale_application_with_incorrect_id(self):
        step("Scale application with incorrect id")
        incorrect_id = "wrong_id"
        expected_message = ApiServiceHttpStatus.MSG_CANNOT_FETCH_INSTANCE.format(incorrect_id)
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, expected_message,
                                     ApiService.scale_application, incorrect_id, 3)

    def test_cannot_scale_application_with_incorrect_instance_number(self):
        step("Scale application with incorrect replicas number")
        assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST, ApiServiceHttpStatus.MSG_INCORRECT_TYPE,
                                     ApiService.scale_application, 3, "wrong_number")
