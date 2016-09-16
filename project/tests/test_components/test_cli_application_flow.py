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

from modules import command
from modules.constants import TapComponent as TAP, Urls
from modules.markers import incremental, priority
from modules.tap_logger import step
from modules.tap_object_model.k8s_application import K8sApplication
from modules.test_names import generate_test_object_name

logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]

APP_INSTANCES = 1
SCALE_APP_INSTANCES = "3"


@priority.high
class TestCheckAppPushHelp:
    def test_check_app_push_help(self, tap_cli):
        step("Check output from tap cli push help")
        output = tap_cli.push_help()
        assert "NAME" in output
        assert "USAGE" in output


@priority.high
class TestCliCommandsWithNonExistingApplication:
    NON_EXISTING_APP_NAME = "non_existing_app_name_{}".format(generate_test_object_name())
    CANNOT_FIND_MSG = "cannot find instance with name: {}".format(NON_EXISTING_APP_NAME)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_try_stop_non_existing_app(self, tap_cli, cli_login):
        step("Try to stop app with non existing name")
        stop = tap_cli.stop_app(application_name=self.NON_EXISTING_APP_NAME)
        assert self.CANNOT_FIND_MSG in stop

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_try_start_non_existing_app(self, tap_cli, cli_login):
        step("Try to start app with non existing name")
        start = tap_cli.start_app(application_name=self.NON_EXISTING_APP_NAME)
        assert self.CANNOT_FIND_MSG in start

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_try_scale_non_existing_app(self, tap_cli, cli_login):
        step("Try to scale app with non existing name")
        scale = tap_cli.scale_app(application_name=self.NON_EXISTING_APP_NAME, instances=SCALE_APP_INSTANCES)
        assert self.CANNOT_FIND_MSG in scale

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_try_check_logs_for_non_existing_app(self, tap_cli, cli_login):
        step("Try to check logs for non existing app name")
        logs = tap_cli.app_logs(application_name=self.NON_EXISTING_APP_NAME)
        assert self.CANNOT_FIND_MSG in logs

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_try_delete_non_existing_app(self, tap_cli, cli_login):
        step("Try to delete with non existing app name")
        delete = tap_cli.delete_app(application_name=self.NON_EXISTING_APP_NAME)
        assert self.CANNOT_FIND_MSG in delete


@incremental
@priority.high
class TestPythonApplicationCliFlow:
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    APP_NAME = "samplepythonapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "PYTHON"
    EXPECTED_FILE_LIST = ["requirements.txt", "run.sh", "src", "vendor"]
    APP_URL_MESSAGE = "TEST APP v.1.0 READY"

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

    def test_0_check_sample_app_content(self, sample_app_tar_content):
        step("Check content of the archive")
        missing_files = [app_file for app_file in self.EXPECTED_FILE_LIST if app_file not in sample_app_tar_content]
        assert len(missing_files) == 0, "Missing files: {}".format(", ".join(missing_files))

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] Cannot log in to tap using tap cli")
    def test_1_push_app(self, cli_login, sample_manifest_path, tap_cli, sample_app_target_directory):
        step("Prepare manifest with parameters")
        manifest_params = {
            'instances': APP_INSTANCES,
            'name': self.APP_NAME,
            'type': self.APP_TYPE
        }
        K8sApplication.update_manifest(sample_manifest_path, manifest_params)
        shutil.copyfile(sample_manifest_path, os.path.join(sample_app_target_directory, "manifest.json"))
        step("Push sample application: {}".format(self.SAMPLE_APP_TAR_NAME))
        push = tap_cli.push(app_dir_path=sample_app_target_directory)
        step("Check headers")
        assert all(self.i in push for self.i in ["NAME", "IMAGE ID", "DESCRIPTION", "REPLICATION"]),\
            "{} header is missing".format(self.i)

    def test_2_ensure_app_is_on_the_list(self, tap_cli, cli_login):
        step("Ensure app is on the list of apps")
        tap_cli.ensure_app_availability_on_the_list(application_name=self.APP_NAME, should_be_on_the_list=True)

    def test_3_ensure_app_is_running(self, tap_cli, cli_login):
        step("Ensure app is running")
        tap_cli.ensure_app_state(application_name=self.APP_NAME, state=K8sApplication.STATE_RUNNING)

    def test_4_ensure_app_is_ready_and_check_app_url_content(self, tap_cli, cli_login):
        step("Get app url")
        app = tap_cli.app(application_name=self.APP_NAME)
        app_url = app["urls"][0]
        step("Ensure app is ready")
        tap_cli.ensure_app_is_ready(application_url=app_url)
        step("Check application url content")
        content = command.run(["curl", app_url])
        assert self.APP_URL_MESSAGE in content

    def test_5_stop_app(self, tap_cli, cli_login):
        step("Stop app")
        stop = tap_cli.stop_app(application_name=self.APP_NAME)
        assert "success" in stop
        step("Ensure app is stopped")
        tap_cli.ensure_app_state(application_name=self.APP_NAME, state=K8sApplication.STATE_STOPPED)

    def test_6_start_app(self, tap_cli, cli_login):
        step("Start app")
        start = tap_cli.start_app(application_name=self.APP_NAME)
        assert "success" in start
        step("Ensure app is running")
        tap_cli.ensure_app_state(application_name=self.APP_NAME, state=K8sApplication.STATE_RUNNING)

    def test_7_scale_app(self, tap_cli, cli_login):
        step("Scale app")
        scale = tap_cli.scale_app(application_name=self.APP_NAME, instances=SCALE_APP_INSTANCES)
        assert "success" in scale
        step("Ensure app is running")
        tap_cli.ensure_app_state(application_name=self.APP_NAME, state=K8sApplication.STATE_RUNNING)

    def test_8_check_app_logs(self, tap_cli, cli_login):
        step("Check logs")
        logs = tap_cli.app_logs(application_name=self.APP_NAME)
        assert self.APP_NAME in logs

    def test_9_delete_app(self, tap_cli, cli_login):
        step("Delete app")
        delete = tap_cli.delete_app(application_name=self.APP_NAME)
        assert "CODE: 204 BODY" in delete

    def test_10_ensure_app_is_not_on_the_list(self, tap_cli, cli_login):
        step("Ensure app is not on the list of apps")
        tap_cli.ensure_app_availability_on_the_list(application_name=self.APP_NAME, should_be_on_the_list=False)


@incremental
@priority.high
class TestGoApplicationCliFlow(TestPythonApplicationCliFlow):
    SAMPLE_APP_TAR_NAME = "tapng-sample-go-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_go_app_url
    APP_NAME = "samplegoapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "GO"
    EXPECTED_FILE_LIST = ["main", "run.sh"]
    APP_URL_MESSAGE = "OK"


@incremental
@priority.high
class TestJavaApplicationCliFlow(TestPythonApplicationCliFlow):
    SAMPLE_APP_TAR_NAME = "tapng-sample-java-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_java_app_url
    APP_NAME = "samplejavaapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "JAVA"
    EXPECTED_FILE_LIST = ["tapng-java-sample-app-0.1.0.jar", "run.sh"]
    APP_URL_MESSAGE = "OK"


@incremental
@priority.high
@pytest.mark.skip("DPNG-10806 [TAP-NG] 413 or 504 for pushing application")
class TestNodeJsApplicationCliFlow(TestPythonApplicationCliFlow):
    SAMPLE_APP_TAR_NAME = "tapng-sample-nodejs-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_nodejs_app_url
    APP_NAME = "samplenodejsapp{}".format(generate_test_object_name().replace('_', ''))
    APP_TYPE = "NODEJS"
    EXPECTED_FILE_LIST = ["server.js", "run.sh", "public", "views", "app", "node_modules", "manifest.yml",
                          "package.json", "README.md"]
    APP_URL_MESSAGE = "This is a Cloud Foundry sample application."
