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

from modules.constants import TapApplicationType, TapEntityState
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CliApplication
from modules.tap_object_model.prep_app import PrepApp
from tests.fixtures.data_repo import DataFileKeys
from tests.test_components.tap_cli.test_cli_application import TestAppBase


class TestPythonCliApp(TestAppBase):

    @priority.high
    def test_push_and_delete_sample_app(self, context, sample_app_target_directory, tap_cli):
        """
        <b>Description:</b>
        Push sample application, check it's show in applications list and remove it.

        <b>Input data:</b>
        1. Sample application target directory

        <b>Expected results:</b>
        Test passes when application is pushed, displayed in applications list and then successfully deleted.

        <b>Steps:</b>
        1. Update application manifest.
        2. Push application.
        3. Verify that application is present in applications list.
        4. Check that application is running.
        5. Check that application is ready.
        6. Delete application.
        7. Check that application is no longer presented in applications list.
        """
        step("Update the manifest")
        p_a = PrepApp(sample_app_target_directory)
        manifest_params = {"type": self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push application")
        application = CliApplication.push(context, tap_cli=tap_cli, app_type=self.APP_TYPE,
                                          app_path=sample_app_target_directory,
                                          name=p_a.app_name, instances=p_a.instances)
        step("Ensure app is on the app list")
        application.ensure_on_app_list()
        step("Ensure app is running")
        application.ensure_app_state(state=TapEntityState.RUNNING)
        step("Ensure app is ready")
        application.ensure_app_is_ready()

        step("Stop application")
        application.stop()
        application.ensure_app_state(state=TapEntityState.STOPPED)
        step("Delete app")
        application.delete()
        step("Ensure app is not on the app list")
        application.ensure_not_on_app_list()

    @pytest.mark.bugs("DPNG-12158 Tap client fails when pushing directory containing symbolic links")
    def test_push_and_delete_sample_app_with_symlinks(self, context, sample_app_target_directory_with_symlinks, tap_cli):
        """
        <b>Description:</b>
        Push sample application, check it's show in applications list and remove it.

        <b>Input data:</b>
        1. Sample application with symlinks target directory

        <b>Expected results:</b>
        Test passes when application is pushed, displayed in applications list and then successfully deleted.

        <b>Steps:</b>
        1. Update application manifest.
        2. Push application.
        3. Verify that application is present in applications list.
        4. Check that application is running.
        5. Check that application is ready.
        6. Delete application.
        7. Check that application is no longer presented in applications list.
        """
        step("Update the manifest")
        p_a = PrepApp(sample_app_target_directory_with_symlinks)
        manifest_params = {"type": self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push application")
        application = CliApplication.push(context, tap_cli=tap_cli, app_type=self.APP_TYPE,
                                          app_path=sample_app_target_directory_with_symlinks,
                                          name=p_a.app_name, instances=p_a.instances)
        step("Ensure app is on the app list")
        application.ensure_on_app_list()
        step("Ensure app is running")
        application.ensure_app_state(state=TapEntityState.RUNNING)
        step("Ensure app is ready")
        application.ensure_app_is_ready()

        step("Stop application")
        application.stop()
        application.ensure_app_state(state=TapEntityState.STOPPED)
        step("Delete app")
        application.delete()
        step("Ensure app is not on the app list")
        application.ensure_not_on_app_list()

    @priority.high
    def test_stop_and_start_app(self, sample_cli_app):
        """
        <b>Description:</b>
        Check that application can be stopped and started again.

        <b>Input data:</b>
        1. Sample application

        <b>Expected results:</b>
        Test passes when application is stopped and successfully started again.

        <b>Steps:</b>
        1. Stop application.
        2. Check that application is stopped.
        3. Start application.
        4. Check that application is running.
        """
        step("Stop app")
        sample_cli_app.stop()
        step("Ensure app is stopped")
        sample_cli_app.ensure_app_state(state=TapEntityState.STOPPED)
        step("Start app")
        sample_cli_app.start()
        step("Ensure app is running")
        sample_cli_app.ensure_app_state(state=TapEntityState.RUNNING)

    def test_restart_app(self, sample_cli_app):
        step("Restart app")
        sample_cli_app.restart()
        step("Ensure app is running")
        sample_cli_app.ensure_app_state(state=TapEntityState.RUNNING)

    @priority.high
    def test_scale_app(self, sample_cli_app):
        """
        <b>Description:</b>
        Check that application can be scaled.

        <b>Input data:</b>
        1. Sample application

        <b>Expected results:</b>
        Test passes when application can be successfully scaled.

        <b>Steps:</b>
        1. Scale application to 3 instances.
        2. Check that application is running.
        3. Verify that there is 3 application instances.
        4. Scale application to 1 instance.
        5. Check that application is running.
        6. Verify that there is 1 application instance.
        """
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

    @priority.medium
    def test_check_app_logs(self, sample_cli_app):
        """
        <b>Description:</b>
        Check that logs of application are properly presented.

        <b>Input data:</b>
        1. Sample application

        <b>Expected results:</b>
        Test passes when logs of application are properly presented.

        <b>Steps:</b>
        1. Check that application name is shown in application logs.
        """
        step("Check logs")
        assert sample_cli_app.name in sample_cli_app.logs()


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestGoCliApp(TestPythonCliApp):
    SAMPLE_APP_NAME = DataFileKeys.TAPNG_GO_APP
    APP_TYPE = TapApplicationType.GO
    EXPECTED_FILE_LIST = ["main", "run.sh"]
    APP_URL_MESSAGE = "OK"


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestJavaCliApp(TestPythonCliApp):
    SAMPLE_APP_NAME = DataFileKeys.TAPNG_JAVA_APP
    APP_TYPE = TapApplicationType.JAVA
    EXPECTED_FILE_LIST = ["tapng-java-sample-app-0.1.0.jar", "run.sh"]
    APP_URL_MESSAGE = "OK"


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestNodeJsCliApp(TestPythonCliApp):
    SAMPLE_APP_NAME = DataFileKeys.TAPNG_NODEJS_APP
    APP_TYPE = TapApplicationType.NODEJS
    EXPECTED_FILE_LIST = ["server.js", "run.sh", "public", "views", "app", "node_modules", "manifest.yml",
                          "package.json", "README.md"]
    APP_URL_MESSAGE = "This is a Cloud Foundry sample application."
