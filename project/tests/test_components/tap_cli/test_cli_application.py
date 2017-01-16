#
# Copyright (c) 2017 Intel Corporation
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
import shutil

import pytest

from modules.constants import TapComponent as TAP, TapApplicationType, TapMessage, TapEntityState
from modules.file_utils import TMP_FILE_DIR
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CliApplication
from modules.tap_object_model.prep_app import PrepApp
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_command_execution_exception
from tests.fixtures.sample_apps import SampleAppKeys

pytestmark = [pytest.mark.components(TAP.cli)]


class TestCheckAppPushHelp: #TODO what about other application commands helps?

    @priority.medium
    def test_check_app_push_help(self, tap_cli):
        """
        <b>Description:</b>
        Check output from tap cli help push.

        <b>Input data:</b>
        1. Command name: application push --help

        <b>Expected results:</b>
        Test passes when TAP CLI help push command print proper output.

        <b>Steps:</b>
        1. Run TAP CLI with command: application push --help.
        2. Verify response contains proper output.
        """
        step("Check output from tap cli push help")
        output = tap_cli.app_push_help()
        assert "NAME" in output
        assert "USAGE" in output


@pytest.mark.usefixtures("cli_login")
class TestCliCommandsWithNonExistingApplication:
    NON_EXISTING_APP_NAME = "non_existing_app_name_{}".format(generate_test_object_name())
    CANNOT_FIND_APP = TapMessage.CANNOT_FIND_APPLICATION_WITH_NAME.format(NON_EXISTING_APP_NAME)
    CANNOT_FIND_MSG = TapMessage.CANNOT_FIND_INSTANCE_WITH_NAME.format(NON_EXISTING_APP_NAME)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] API service doesn't accept SSL, cannot log in to tap with TAP CLI using api url without specified protocol")
    @priority.low
    def test_try_stop_non_existing_app(self, tap_cli):
        """
        <b>Description:</b>
        Try to stop non existing application.

        <b>Input data:</b>
        1. Command name: application stop --name <non_existing_name>
        2. Name of non existing application

        <b>Expected results:</b>
        Test passes when attempt to stop non existing application returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command: application stop --name <non_existing_name>.
        2. Verify that attempt to stop non existing application return expected error message.
        """
        step("Try to stop app with non existing name")
        assert_raises_command_execution_exception(1, self.CANNOT_FIND_MSG, tap_cli.app_stop,
                                                  application_name=self.NON_EXISTING_APP_NAME)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] API service doesn't accept SSL, cannot log in to tap with TAP CLI using api url without specified protocol")
    @priority.low
    def test_try_start_non_existing_app(self, tap_cli):
        """
        <b>Description:</b>
        Try to start non existing application.

        <b>Input data:</b>
        1. Command name: application start --name <non_existing_name>
        2. Name of non existing application

        <b>Expected results:</b>
        Test passes when attempt to start non existing application returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command: application start --name <non_existing_name>.
        2. Verify that attempt to start non existing application return expected error message.
        """
        step("Try to start app with non existing name")
        assert_raises_command_execution_exception(1, self.CANNOT_FIND_MSG, tap_cli.app_start,
                                                  application_name=self.NON_EXISTING_APP_NAME)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] API service doesn't accept SSL, cannot log in to tap with TAP CLI using api url without specified protocol")
    @priority.low
    def test_try_restart_non_existing_app(self, tap_cli):
        """
        <b>Description:</b>
        Try to restart non existing application.

        <b>Input data:</b>
        1. Command name: application restart --name <non_existing_name>
        2. Name of non existing application

        <b>Expected results:</b>
        Test passes when attempt to restart non existing application returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command: application restart --name <non_existing_name>.
        2. Verify that attempt to restart non existing application return expected error message.
        """
        step("Try to restart app with non existing name")
        assert_raises_command_execution_exception(1, self.CANNOT_FIND_MSG, tap_cli.app_restart,
                                                  application_name=self.NON_EXISTING_APP_NAME)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] API service doesn't accept SSL, cannot log in to tap with TAP CLI using api url without specified protocol")
    @priority.low
    def test_try_scale_non_existing_app(self, tap_cli):
        """
        <b>Description:</b>
        Try to scale non existing application.

        <b>Input data:</b>
        1. Command scale: application scale --name <non_existing_name> --replicas <number_of_replicas>
        2. Name of non existing application
        3. Number of replicas

        <b>Expected results:</b>
        Test passes when attempt to scale non existing application returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command: application scale --name <non_existing_name> --replicas <number_of_replicas>.
        2. Verify that attempt to scale non existing application return expected error message.
        """
        scaled_instances = '3'
        step("Try to scale app with non existing name")
        assert_raises_command_execution_exception(1, self.CANNOT_FIND_MSG, tap_cli.app_scale,
                                                  application_name=self.NON_EXISTING_APP_NAME,
                                                  instances=scaled_instances)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] API service doesn't accept SSL, cannot log in to tap with TAP CLI using api url without specified protocol")
    @priority.low
    def test_try_get_details_info_non_existing_app(self, tap_cli):
        """
        <b>Description:</b>
        Try to get details info about non existing application.

        <b>Input data:</b>
        1. Command name: application info --name <non_existing_name>
        2. Name of non existing application

        <b>Expected results:</b>
        Test passes when attempt to get info about non existing application returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command: application info --name <non_existing_name>.
        2. Verify that attempt to get details info about non existing application return expected error message.
        """
        step("Try to get details info about app with non existing name")
        assert_raises_command_execution_exception(1, self.CANNOT_FIND_APP, tap_cli.app_info,
                                                  application_name=self.NON_EXISTING_APP_NAME)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] API service doesn't accept SSL, cannot log in to tap with TAP CLI using api url without specified protocol")
    @priority.low
    def test_try_check_logs_for_non_existing_app(self, tap_cli):
        """
        <b>Description:</b>
        Try to retrieve logs of non existing application.

        <b>Input data:</b>
        1. Command name: application logs show --name <non_existing_name>
        2. Name of non existing application

        <b>Expected results:</b>
        Test passes when attempt to retrieve logs of non existing application returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command: application logs show --name <non_existing_name>.
        2. Verify that attempt to retrieve logs for non existing application return expected message.
        """
        step("Try to check logs for non existing app name")
        assert_raises_command_execution_exception(1, self.CANNOT_FIND_MSG, tap_cli.app_logs,
                                                  application_name=self.NON_EXISTING_APP_NAME)

    @pytest.mark.bugs("DPNG-11419 [TAP-NG] API service doesn't accept SSL, cannot log in to tap with TAP CLI using api url without specified protocol")
    @priority.low
    def test_try_delete_non_existing_app(self, tap_cli):
        """
        <b>Description:</b>
        Try to delete non existing application.

        <b>Input data:</b>
        1. Command name: application delete --name <non_existing_name>
        2. Name of non existing application

        <b>Expected results:</b>
        Test passes when attempt to delete non existing application returns proper message.

        <b>Steps:</b>
        1. Run TAP CLI with command: application delete --name <non_existing_name>.
        2. Verify that attempt to delete non existing application return expected error message.
        """
        step("Try to delete app with non existing name")
        assert_raises_command_execution_exception(1, self.CANNOT_FIND_MSG, tap_cli.app_delete,
                                                  application_name=self.NON_EXISTING_APP_NAME)


class TestAppBase:
    SAMPLE_APP_NAME = SampleAppKeys.TAPNG_PYTHON_APP
    APP_TYPE = TapApplicationType.PYTHON27
    EXPECTED_FILE_LIST = ["requirements.txt", "run.sh", "vendor"]
    APP_URL_MESSAGE = "TEST APP v.1.0 READY"

    @pytest.yield_fixture(scope="class")
    def sample_app_source_dir(self, test_sample_apps):
        """ Download and extract sample application. The archive may contain symbolic links. """
        sample_app_source_dir = os.path.join(TMP_FILE_DIR, test_sample_apps[self.SAMPLE_APP_NAME].filename)
        step("Extract application archive")
        with tarfile.open(test_sample_apps[self.SAMPLE_APP_NAME].filepath) as tar:
            tar.extractall(path=sample_app_source_dir)
            sample_app_tar_content = [name.replace("./", "", 1) for name in tar.getnames()]
        step("Check content of the archive")
        missing_files = [app_file for app_file in self.EXPECTED_FILE_LIST if app_file not in sample_app_tar_content]
        assert len(missing_files) == 0, "Missing files: {}".format(", ".join(missing_files))
        yield sample_app_source_dir
        # Fixture finalization
        shutil.rmtree(sample_app_source_dir, ignore_errors=True)

    @pytest.yield_fixture(scope="class")
    def sample_app_target_directory(self, sample_app_source_dir):
        """ Prepare sample application directory WITHOUT symbolic links """

        sample_app_target_directory = os.path.join(os.path.dirname(os.path.normpath(sample_app_source_dir)),
                                                   "sample_{}_app_target".format(self.APP_TYPE))
        step("Make copy of application directory with symbolic links dereferenced")
        shutil.rmtree(sample_app_target_directory, ignore_errors=True)
        shutil.copytree(sample_app_source_dir,
                        sample_app_target_directory,
                        symlinks=False)
        yield sample_app_target_directory
        # Fixture finalization
        shutil.rmtree(sample_app_target_directory, ignore_errors=True)

    @pytest.yield_fixture(scope="class")
    def sample_app_target_directory_with_symlinks(self, sample_app_source_dir):
        """ Prepare sample application directory WITH symbolic links """

        sample_app_target_directory_with_symlinks = os.path.join(os.path.dirname(os.path.normpath(sample_app_source_dir)),
                                                                 "sample_{}_app_target_with_symlinks".format(self.APP_TYPE))
        step("Make copy of application directory with symbolic links preserved")
        shutil.rmtree(sample_app_target_directory_with_symlinks, ignore_errors=True)
        shutil.copytree(sample_app_source_dir,
                        sample_app_target_directory_with_symlinks,
                        symlinks=True)
        step("Create internal directory symlink")
        runfile_name = "run.sh"
        runfile_copy_name = "test-copy-of-{}".format(runfile_name)
        runfile = os.path.join(sample_app_target_directory_with_symlinks, runfile_name)
        runfile_copy = os.path.join(sample_app_target_directory_with_symlinks, runfile_copy_name)
        shutil.move(src=runfile, dst=runfile_copy)
        os.symlink(src=runfile_copy_name, dst=runfile) # create relative symbolic link - no absolute target path
        yield sample_app_target_directory_with_symlinks
        # Fixture finalization
        shutil.rmtree(sample_app_target_directory_with_symlinks, ignore_errors=True)

    @pytest.fixture(scope="class")
    def sample_cli_app(self, class_context, sample_app_target_directory, tap_cli):
        step("Update the manifest")
        p_a = PrepApp(sample_app_target_directory)
        manifest_params = {"type": self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push application")
        application = CliApplication.push(class_context, tap_cli=tap_cli, app_type=self.APP_TYPE,
                                          app_path=sample_app_target_directory,
                                          name=p_a.app_name, instances=p_a.instances)
        step("Ensure app is on the app list")
        application.ensure_on_app_list()
        step("Ensure app is running")
        application.ensure_app_state(state=TapEntityState.RUNNING)
        step("Ensure app is ready")
        application.ensure_app_is_ready()
        return application


@pytest.mark.usefixtures("cli_login")
class TestPythonCliApp(TestAppBase):

    @priority.high
    def test_push_and_delete_sample_app(self, context, sample_app_target_directory, tap_cli):
        """
        <b>Description:</b>
        Push sample application, check it's show in applications list and remove it.

        <b>Input data:</b>
        1. Sample application target directory

        <b>Expected results:</b>
        Test passes when application is pushed, displayed in applications list,
        contained proper key-value pairs in details info and then successfully deleted.

        <b>Steps:</b>
        1. Update application manifest.
        2. Push application.
        3. Verify that application is present in applications list.
        4. Check that application is running.
        5. Check that application is ready.
        6. Check if details info about pushed application is correct.
        7. Stop application
        8. Check that application is stopped.
        9. Delete application.
        10. Check that application is no longer presented in applications list.
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
        step("Ensure details info about application is correct")
        application.ensure_info_about_app_was_correct(p_a.app_name, self.APP_TYPE)
        step("Stop application")
        application.stop()
        application.ensure_app_state(state=TapEntityState.STOPPED)
        step("Delete app")
        application.delete()
        step("Ensure app is not on the app list")
        application.ensure_not_on_app_list()

    def test_push_and_delete_sample_app_with_symlinks(self, context, sample_app_target_directory_with_symlinks, tap_cli):
        """
        <b>Description:</b>
        Push sample application, check it's show in applications list, verify it contains proper key-value pairs
        in details info and remove it.

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
        6. Check if details info about pushed application is correct.
        7. Stop application
        8. Check that application is stopped.
        9. Delete application.
        10. Check that application is no longer presented in applications list.
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
        step("Ensure details info about application is correct")
        application.ensure_info_about_app_was_correct(p_a.app_name, self.APP_TYPE)
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

    @priority.high
    def test_restart_app(self, sample_cli_app):
        """
        <b>Description:</b>
        Check that application is in RUNNING state after restart.

        <b>Input data:</b>
        1. Sample application

        <b>Expected results:</b>
        Test passes when application is restarted successfully.

        <b>Steps:</b>
        1. Push application.
        2. Verify that application is present in applications list.
        3. Check that application is running.
        4. Check that application is ready.
        5. Restart application.
        6. Check that application is running.
        """
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
    def test_try_to_delete_app_in_running_state(self, sample_cli_app):
        """
        <b>Description:</b>
        Push sample application and wait until it state is running. Then try to delete application in RUNNING state.

        <b>Input data:</b>
        1. Sample application

        <b>Expected results:</b>
        Test passes when trying to delete application in RUNNING state causes an error.

        <b>Steps:</b>
        1. Push application.
        2. Verify that application is present in applications list.
        3. Check that application is running.
        4. Check that application is ready.
        5. Try to delete application.
        """
        step("Try to delete application in running state")
        assert_raises_command_execution_exception(1, TapMessage.CANNOT_DELETE_APPLICATION_IN_RUNNING_STATE,
                                                  sample_cli_app.delete)

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
        1. Check that application logs are shown.
        """
        step("Check logs")
        assert sample_cli_app.logs().strip()

    @priority.medium
    def test_try_to_push_same_application_twice(self, context, sample_cli_app, tap_cli):
        """
        <b>Description:</b>
        Push sample application and wait until it state is running. Then try to push same application again.

        <b>Input data:</b>
        1. Sample application

        <b>Expected results:</b>
        Test passes when application is pushed and is in running state and trying to push same application again causes
        an error.

        <b>Steps:</b>
        1. Push application.
        2. Verify that application is present in applications list.
        3. Check that application is running.
        4. Check that application is ready.
        5. Try to push same application again.
        """
        step("Try to push same application again")
        assert_raises_command_execution_exception(1, TapMessage.APPLICATION_ALREADY_EXISTS,
                                                  CliApplication.push,
                                                  context, tap_cli=tap_cli,
                                                  app_type=sample_cli_app.app_type,
                                                  app_path=sample_cli_app.target_directory,
                                                  name=sample_cli_app.name,
                                                  instances=sample_cli_app.instances)


@pytest.mark.usefixtures("cli_login")
class TestBadApplication(TestAppBase):
    INVALID_APP_NAME = 'invalid_name'

    @priority.medium
    def test_no_manifest(self, class_context, tap_cli, sample_app_target_directory):
        """
        <b>Description:</b>
        Try to push an application, but don't provide the manifest.

        <b>Input data:</b>
        1. Sample application without manifest.json

        <b>Expected results:</b>
        Test passes when attempt to push application without providing manifest.json returns proper message.

        <b>Steps:</b>
        1. Prepare directory with sample application.
        2. Remove manifest.json from prepared directory.
        3. Try to push application.
        """
        app_name = "app-test-name"
        step("prepare directory with sample application")
        p_a = PrepApp(sample_app_target_directory)
        step("remove manifest.json from prepared directory")
        manifest_path = os.path.join(sample_app_target_directory, p_a.MANIFEST_NAME)
        os.remove(manifest_path)
        step("try to push application")
        assert_raises_command_execution_exception(1, TapMessage.CANNOT_FIND_MANIFEST,
                                                  CliApplication.push,
                                                  class_context, tap_cli=tap_cli,
                                                  app_type=self.APP_TYPE,
                                                  app_path=p_a.app_path,
                                                  name=app_name,
                                                  instances=p_a.instances)

    @priority.low
    def test_try_push_app_with_invalid_manifest(self, class_context, tap_cli, sample_app_target_directory):
        """
        <b>Description:</b>
        Try to push an application with invalid manifest.

        <b>Input data:</b>
        1. Sample application with invalid manifest.json

        <b>Expected results:</b>
        Test passes when attempt to push application with invalid app name in manifest.json returns proper message.

        <b>Steps:</b>
        1. Prepare directory with sample application.
        2. Update manifest.json with invalid app name.
        3. Try to push application with wrong manifest.json.
        """
        step("prepare directory with sample application")
        p_a = PrepApp(sample_app_target_directory)
        step("update manifest.json to contain improper app name")
        manifest_params = {"name": self.INVALID_APP_NAME, "type": self.APP_TYPE}
        p_a.update_manifest(params=manifest_params)
        assert_raises_command_execution_exception(1, TapMessage.MANIFEST_JSON_INCORRECT_NAME_VALUE.format(self.INVALID_APP_NAME),
                                                  CliApplication.push,
                                                  class_context, tap_cli=tap_cli,
                                                  app_type=self.APP_TYPE,
                                                  app_path=p_a.app_path,
                                                  name=p_a.app_name,
                                                  instances=p_a.instances)
#TODO test_application_help
