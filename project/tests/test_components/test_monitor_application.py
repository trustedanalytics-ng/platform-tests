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

from modules.constants import TapComponent as TAP, TapApplicationType
from modules.file_utils import TMP_FILE_DIR
from modules.tap_logger import step
from modules.tap_object_model import CliApplication
from modules.tap_object_model.prep_app import PrepApp
from modules.http_calls.kubernetes import k8s_get_pods, k8s_logs
from tests.fixtures.data_repo import DataFileKeys

pytestmark = [pytest.mark.components(TAP.cli, TAP.monitor)]


@pytest.mark.usefixtures("open_tunnel")
@pytest.mark.usefixtures("cli_login")
class TestMonitorApplication:
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    APP_TYPE = TapApplicationType.PYTHON27
    EXPECTED_FILE_LIST = ["requirements.txt", "run.sh", "src", "vendor"]
    POD_APP_NAME = TAP.container_broker
    LOG_TIME_SEC = 600

    @pytest.fixture(scope="class")
    def sample_app_target_directory(self, test_data_urls):
        return os.path.join(TMP_FILE_DIR, test_data_urls[DataFileKeys.TAPNG_PYTHON_APP].filename)

    @pytest.fixture(scope="class")
    def sample_app_tar_content(self, request, test_data_urls, sample_app_target_directory):
        step("Extract application archive")

        with tarfile.open(test_data_urls[DataFileKeys.TAPNG_PYTHON_APP].filepath) as tar:
            tar.extractall(path=sample_app_target_directory)
            file_list = [name.replace("./", "", 1) for name in tar.getnames()]

        request.addfinalizer(lambda: shutil.rmtree(sample_app_target_directory))

        return file_list

    def test_app_deployment(self, context, sample_app_target_directory, tap_cli, sample_app_tar_content):
        """
        <b>Description:</b>
        Check monitor during app deployment

        <b>Input data:</b>
        Sample application

        <b>Expected results:</b>
        Monitor logs can be retrieved

        <b>Steps:</b>
        - Update application manifest
        - Push the application and wait for it to receive id
        - Retrieve applicaiton logs
        - Verify presence of monitor logs
        """
        step("Update the manifest")
        p_a = PrepApp(sample_app_target_directory)
        manifest_params = {"type" : self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push sample application: {}".format(self.SAMPLE_APP_TAR_NAME))
        application = CliApplication.push(context, tap_cli=tap_cli, app_type=self.APP_TYPE,
                                          app_path=sample_app_target_directory,
                                          name=p_a.app_name, instances=p_a.instances)

        app_id = application.ensure_app_has_id()
        step("Get K8s pods")
        pods_list = k8s_get_pods()
        step("Ensure app is on the list of apps")
        pods_json = [i["metadata"] for i in pods_list["items"]]
        container_broker_name = [i["name"] for i in pods_json if self.POD_APP_NAME in i["name"]]
        step("Collect logs for container-broker")
        log = k8s_logs(container_broker_name[0], {"sinceSeconds": self.LOG_TIME_SEC,
                                                  "container": "container-broker"})
        log_entries = log.split('\n')
        assert (i for i in log_entries if "[MonitorInstanceDeployment]" in i and """InstanceId: {}""".format(app_id))
