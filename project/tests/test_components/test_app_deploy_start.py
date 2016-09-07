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

import codecs
import json
import re

import pytest

import config
from modules.constants import HttpStatus
from modules.constants import TapComponent as TAP
from modules.constants.urls import Urls
from modules.file_utils import download_file
from modules.http_calls.kubernetes import k8s_get_pods
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
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    APP_NAME = "samplepythonapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "PYTHON"

    APP_INSTANCES = 1
    MANIFEST_NAME = "manifest.json"
    application = None
    application_file_path = None
    manifest_file_path = None

    @pytest.fixture(scope="class")
    def python_app_path(self):
        self.__class__.application_file_path = download_file(self.SAMPLE_APP_URL, self.SAMPLE_APP_TAR_NAME)
        return self.application_file_path

    @pytest.fixture(scope="class")
    def manifest_path(self):
        self.__class__.manifest_file_path = download_file(Urls.manifest_url, self.MANIFEST_NAME)
        return self.manifest_file_path

    @staticmethod
    def change_json_file_param_value(file_path, manifest_params):
        with codecs.open(file_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            params = json.dumps(manifest_params)
            params = json.loads(params)
            for key in params:
                data[key] = params[key]
            f.seek(0)
            json.dump(data, f, indent=4)

    def test_0_push_application(self, class_context, python_app_path, manifest_path):
        step("Prepare manifest with parameters")
        manifest_params = {
            'instances': self.APP_INSTANCES,
            'name': self.APP_NAME,
            'type': self.APP_TYPE
        }
        self.change_json_file_param_value(manifest_path, manifest_params)
        step("Push sample application: {}".format(self.SAMPLE_APP_TAR_NAME))
        self.__class__.application = K8sApplication.push(class_context, python_app_path, manifest_path)

    def test_1_push_application_with_existing_name(self, class_context):
        step("Push the same application again")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, "",
                                     K8sApplication.push, class_context, self.application_file_path,
                                     self.manifest_file_path)

    def test_2_check_application_url(self):
        step("Check application state")
        self.application.ensure_running()
        step("Check application url")
        self.application.url = "http://{}.{}".format(self.APP_NAME, config.tap_domain)
        self.application.ensure_ready()

    def test_3_stop_application(self):
        step("Stop application")
        response = self.application.stop()
        assert response["message"] == "success"
        self.application.ensure_stopped()
        self.application.ensure_is_down()

    def test_4_start_application(self):
        step("Start application")
        response = self.application.start()
        assert response["message"] == "success"
        self.application.ensure_ready()

    def test_5_check_logs(self):
        step("Check logs of application")
        response = self.application.get_logs()
        assert response.status_code == HttpStatus.CODE_OK

    def test_6_scale_application(self):
        step("Scale application")
        response = self.application.scale(3)
        assert response["message"] == "success"

    def test_7_check_number_of_application_instances(self):
        step("Check number of application instances")
        response = k8s_get_pods()
        pods_json = [i["metadata"] for i in response["items"]]
        labels = [i["labels"] for i in pods_json]
        found_ids = [m.start() for m in re.finditer(self.application.id, labels.__str__())]
        assert len(found_ids) == 3

    def test_8_scale_application_with_wrong_id(self):
        step("Scale application with wrong id")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, "",
                                     ApiService.scale_application, "wrong_id", 3)

    def test_9_scale_application_with_wrong_number(self):
        step("Scale application with wrong replicas number")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, "",
                                     ApiService.scale_application, 3, "wrong_number")

    def test_10_delete_application(self):
        step("Delete application")
        self.application.delete()

    def test_11_check_application_url(self):
        step("Check if application url is unavailable")
        self.application.ensure_is_down()


@incremental
class TestNodeJsApplicationFlow(TestPythonApplicationFlow):
    SAMPLE_APP_TAR_NAME = "tapng-sample-nodejs-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_nodejs_app_url
    APP_NAME = "samplenodejsapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "NODEJS"


@incremental
class TestGoApplicationFlow(TestPythonApplicationFlow):
    SAMPLE_APP_TAR_NAME = "tapng-sample-go-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_go_app_url
    APP_NAME = "samplegoapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "GO"


@incremental
class TestJavaApplicationFlow(TestPythonApplicationFlow):
    SAMPLE_APP_TAR_NAME = "tapng-sample-java-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_java_app_url
    APP_NAME = "samplejavaapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "JAVA"
