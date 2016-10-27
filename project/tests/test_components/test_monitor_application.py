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

import os
import shutil
import tarfile

import pytest

from modules.constants import TapComponent
from modules.constants import TapComponent as TAP, Urls, TapApplicationType
from modules.tap_logger import step
from modules.tap_object_model import CliApplication
from modules.http_calls.kubernetes import k8s_get_pods, k8s_logs

logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]


@pytest.mark.usefixtures("cli_login")
@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestMonitorApplication:
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    APP_TYPE = TapApplicationType.PYTHON27
    EXPECTED_FILE_LIST = ["requirements.txt", "run.sh", "src", "vendor"]
    POD_APP_NAME = TapComponent.container_broker
    LOG_TIME_SEC = 600

    @pytest.fixture(scope="class")
    def sample_app_target_directory(self, sample_app_path):
        sample_app_path = os.path.abspath(sample_app_path)
        return os.path.join(os.path.dirname(sample_app_path), "sample_{}_app".format(self.APP_TYPE))

    @pytest.fixture(scope="class")
    def sample_app_tar_content(self, request, sample_app_path, sample_app_target_directory):
        step("Extract application archive")

        with tarfile.open(sample_app_path) as tar:
            tar.extractall(path=sample_app_target_directory)
            file_list = [name.replace("./", "", 1) for name in tar.getnames()]

        request.addfinalizer(lambda: shutil.rmtree(sample_app_target_directory))

        return file_list

    @pytest.mark.bugs("DPNG-12123 FileNotFoundError: /.kube")
    @pytest.mark.bugs("DPNG-12343 [api-tests] Tests which push app using cli fail immediately instead of waiting")
    def test_app_deployment(self, context, sample_app_target_directory, tap_cli, sample_app_tar_content):
        step("Push sample application: {}".format(self.SAMPLE_APP_TAR_NAME))
        application = CliApplication.push(context, tap_cli=tap_cli, app_type=self.APP_TYPE,
                                          app_path=sample_app_target_directory)
        app_id = application.ensure_app_has_id()
        step("Get K8s pods")
        pods_list = k8s_get_pods()
        step("Ensure app is on the list of apps")
        pods_json = [i["metadata"] for i in pods_list["items"]]
        container_broker_name = [i["name"] for i in pods_json if self.POD_APP_NAME in i["name"]]
        step("Collect logs for container-broker")
        log = k8s_logs(container_broker_name[0], {"sinceSeconds": self.LOG_TIME})
        log_entries = log.split('\n')
        assert (i for i in log_entries if "[MonitorInstanceDeployment]" in i and """InstanceId: {}""".format(app_id))
