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
import tarfile

import pytest

from modules.constants import TapComponent as TAP, Urls, TapApplicationType, TapMessage, TapEntityState
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CliApplication
from modules.test_names import generate_test_object_name

logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]


@priority.medium
class TestCheckAppPushHelp:
    def test_check_app_push_help(self, tap_cli):
        step("Check output from tap cli push help")
        output = tap_cli.push_help()
        assert "NAME" in output
        assert "USAGE" in output


@priority.medium
class TestCliCommandsWithNonExistingApplication:
    NON_EXISTING_APP_NAME = "non_existing_app_name_{}".format(generate_test_object_name())
    CANNOT_FIND_MSG = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(NON_EXISTING_APP_NAME)

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
        scaled_instances = '3'
        step("Try to scale app with non existing name")
        scale = tap_cli.scale_app(application_name=self.NON_EXISTING_APP_NAME, instances=scaled_instances)
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


@priority.high
@pytest.mark.usefixtures("cli_login")
@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestPythonCliApp:
    SAMPLE_APP_TAR_NAME = "tapng-sample-python-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    APP_TYPE = TapApplicationType.PYTHON27
    EXPECTED_FILE_LIST = ["requirements.txt", "run.sh", "src", "vendor"]
    APP_URL_MESSAGE = "TEST APP v.1.0 READY"

    @pytest.fixture(scope="class")
    def sample_app_target_directory(self, sample_app_path):
        sample_app_path = os.path.abspath(sample_app_path)
        return os.path.join(os.path.dirname(sample_app_path), "sample_{}_app".format(self.APP_TYPE))

    @pytest.fixture(scope="class")
    def sample_cli_app(self, class_context, sample_app_target_directory, tap_cli):
        step("Push application")
        application = CliApplication.push(class_context, tap_cli=tap_cli, app_type=self.APP_TYPE,
                                          app_path=sample_app_target_directory)
        step("Ensure app is on the app list")
        application.ensure_on_app_list()
        step("Ensure app is running")
        application.ensure_app_state(state=TapEntityState.RUNNING)
        step("Ensure app is ready")
        application.ensure_app_is_ready()
        return application

    def test_check_sample_app_content(self, sample_app_path, sample_app_target_directory):
        step("Extract application archive")

        with tarfile.open(sample_app_path) as tar:
            tar.extractall(path=sample_app_target_directory)
            sample_app_tar_content = [name.replace("./", "", 1) for name in tar.getnames()]

        step("Check content of the archive")
        missing_files = [app_file for app_file in self.EXPECTED_FILE_LIST if app_file not in sample_app_tar_content]
        assert len(missing_files) == 0, "Missing files: {}".format(", ".join(missing_files))

    def test_push_and_delete_sample_app(self, context, sample_app_target_directory, tap_cli):
        step("Push application")
        application = CliApplication.push(context, tap_cli=tap_cli, app_type=self.APP_TYPE,
                                          app_path=sample_app_target_directory)
        step("Ensure app is on the app list")
        application.ensure_on_app_list()
        step("Ensure app is running")
        application.ensure_app_state(state=TapEntityState.RUNNING)
        step("Ensure app is ready")
        application.ensure_app_is_ready()

        step("Delete app")
        application.delete()
        step("Ensure app is not on the app list")
        application.ensure_not_on_app_list()

    def test_stop_and_start_app(self, sample_cli_app):
        step("Stop app")
        sample_cli_app.stop()
        step("Ensure app is stopped")
        sample_cli_app.ensure_app_state(state=TapEntityState.STOPPED)
        step("Start app")
        sample_cli_app.start()
        step("Ensure app is running")
        sample_cli_app.ensure_app_state(state=TapEntityState.RUNNING)

    def test_scale_app(self, sample_cli_app):
        scaled_instances = '3'
        step("Scale app to {} instance(s)".format(scaled_instances))
        sample_cli_app.scale(scale_app_instances=scaled_instances)
        step("Ensure app is running")
        sample_cli_app.ensure_app_state(state=TapEntityState.RUNNING)
        step("Check there are/is {} instance(s)".format(scaled_instances))
        assert sample_cli_app.get_running_instances() == int(scaled_instances)

        scaled_instances = '1'
        step("Scale app to {} instance(s)".format(scaled_instances))
        sample_cli_app.scale(scale_app_instances=scaled_instances)
        step("Ensure app is running")
        sample_cli_app.ensure_app_state(state=TapEntityState.RUNNING)
        step("Check there are/is {} instance(s)".format(scaled_instances))
        assert sample_cli_app.get_running_instances() == int(scaled_instances)

    def test_check_app_logs(self, sample_cli_app):
        step("Check logs")
        assert sample_cli_app.name in sample_cli_app.logs()


@priority.high
@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestGoCliApp(TestPythonCliApp):
    SAMPLE_APP_TAR_NAME = "tapng-sample-go-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_go_app_url
    APP_TYPE = TapApplicationType.GO
    EXPECTED_FILE_LIST = ["main", "run.sh"]
    APP_URL_MESSAGE = "OK"


@priority.high
@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestJavaCliApp(TestPythonCliApp):
    SAMPLE_APP_TAR_NAME = "tapng-sample-java-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_java_app_url
    APP_TYPE = TapApplicationType.JAVA
    EXPECTED_FILE_LIST = ["tapng-java-sample-app-0.1.0.jar", "run.sh"]
    APP_URL_MESSAGE = "OK"


@priority.high
@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestNodeJsCliApp(TestPythonCliApp):
    SAMPLE_APP_TAR_NAME = "tapng-sample-nodejs-app.tar.gz"
    SAMPLE_APP_URL = Urls.tapng_nodejs_app_url
    APP_TYPE = TapApplicationType.NODEJS
    EXPECTED_FILE_LIST = ["server.js", "run.sh", "public", "views", "app", "node_modules", "manifest.yml",
                          "package.json", "README.md"]
    APP_URL_MESSAGE = "This is a Cloud Foundry sample application."
