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

from modules.constants import TapApplicationType, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Application
from modules.tap_object_model.prep_app import PrepApp
from tests.fixtures import assertions
from tests.fixtures.data_repo import DataFileKeys


logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]


@pytest.mark.usefixtures("open_tunnel")
class ApiServiceApplicationFlow:

    @pytest.fixture(scope="class")
    def sample_application(self, class_context, test_data_urls, api_service_admin_client):
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(test_data_urls[self.SAMPLE_APP].filepath)
        manifest_params = {"type" : self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        log_fixture("Push sample application and check it's running")
        application = Application.push(class_context, app_path=test_data_urls[self.SAMPLE_APP].filepath,
                                       name=p_a.app_name, manifest_path=manifest_path,
                                       client=api_service_admin_client)
        application.ensure_running()
        return application

    @priority.high
    def test_push_and_delete_application(self, context, test_data_urls, api_service_admin_client):
        """
        <b>Description:</b>
        Attempts to push application, stop it and then delete it.

        <b>Input data:</b>
        - Sample application
        - Admin credentials

        <b>Expected results:</b>
        - Application is successfully pushed to platform
        - Apllication is in running state
        - It's possible to stop the application
        - it's possible to remove the application
        - After removal application is no longer available

        <b>Steps:</b>
        - Sample application is downloaded
        - Manifest is updated with unique name
        - Application is pushed to platform using admin
        - It's verified that the application is in running state
        - Application is stopped and it's verified that the application has stopped
        - Remove the application and verify it's no longer available
        """
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(test_data_urls[self.SAMPLE_APP].filepath)
        manifest_params = {"type" : self.APP_TYPE}
        manifest_path = p_a.update_manifest(params=manifest_params)

        step("Push sample application")
        application = Application.push(context, app_path=test_data_urls[self.SAMPLE_APP].filepath,
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
        """
        <b>Description:</b>
        Verifies it's possible to stop and later start the application

        <b>Input data:</b>
        - Sample application

        <b>Expected results:</b>
        - It's possible to stop the application
        - It's possible to start the application
        - After such operations application is running

        <b>Steps:</b>
        - Download and push sample application
        - Stop the application and make sure it's in stopped state
        - Start the application and make sure it's running
        """
        step("Stop application")
        sample_application.stop()
        step("Check that the application is stopped")
        sample_application.ensure_stopped()
        step("Start application")
        sample_application.start()
        step("Check application is ready")
        sample_application.ensure_running()


    @priority.high
    def test_restart_application(self, sample_application):
        """
        <b>Description:</b>
        Restart the application and verify it's running

        <b>Input data:</b>
        - Fixture sample_application that is already pushed application

        <b>Expected results:</b>
        - Application can be restarted
        - Application is running after restart

        <b>Steps:</b>
        - Download and push sample application
        - Restart the application and make sure it's in running state
        """
        step("Restart application")
        sample_application.restart()
        step("Check application is ready")
        sample_application.ensure_running()

    @priority.medium
    def test_get_application_logs(self, sample_application, api_service_admin_client):
        """
        <b>Description:</b>
        Retrieves logs from the application

        <b>Input data:</b>
        - Sample application
        - Admin credentials

        <b>Expected results:</b>
        - Logs from the application are retrieved

        <b>Steps:</b>
        - Download and push sample application
        - Retrieve logs from the application
        """
        step("Check that getting application logs returns no error")
        response = sample_application.get_logs(client=api_service_admin_client)
        # TODO assert something more meaningful
        assert type(response) is dict

    @priority.medium
    def test_scale_application(self, sample_application, api_service_admin_client):
        """
        <b>Description:</b>
        Scales the application and verifies that it was scaled

        <b>Input data:</b>
        - Sample application
        - Admin credentials

        <b>Expected results:</b>
        - It's possible to scale application

        <b>Steps:</b>
        - Download and push sample application
        - scale application and verifies that application was scaled by checking
          the replication amount
        """
        step("Scale application")
        replicas_number = 3
        response = sample_application.scale(replicas=replicas_number, client=api_service_admin_client)
        step("Check number of application instances")
        app_info = Application.get(sample_application.id, client=api_service_admin_client)
        assert app_info.running_instances == replicas_number


class TestPythonApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP = DataFileKeys.TAPNG_PYTHON_APP
    APP_TYPE = TapApplicationType.PYTHON27


class TestNodeJsApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP = DataFileKeys.TAPNG_NODEJS_APP
    APP_TYPE = TapApplicationType.NODEJS


class TestGoApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP = DataFileKeys.TAPNG_GO_APP
    APP_TYPE = TapApplicationType.GO


class TestJavaApplicationFlow(ApiServiceApplicationFlow):
    SAMPLE_APP = DataFileKeys.TAPNG_JAVA_APP
    APP_TYPE = TapApplicationType.JAVA
