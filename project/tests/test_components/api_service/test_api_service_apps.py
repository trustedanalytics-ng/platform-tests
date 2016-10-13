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

from modules.constants import ApiServiceHttpStatus, TapApplicationType, Urls, TapEntityState, TapComponent as TAP
from modules.http_calls.platform import api_service, catalog as catalog_api
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Application
from tests.fixtures import assertions


logged_components = (TAP.api_service,)
pytestmark = [pytest.mark.components(TAP.api_service)]


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestApiServiceApplication:
    SAMPLE_APP_URL = Urls.tapng_python_app_url

    @pytest.fixture(scope="class")
    def sample_app(self, class_context, sample_app_path, tap_cli):
        log_fixture("Push sample application")
        application = Application.push(class_context, app_path=sample_app_path, tap_cli=tap_cli,
                                       app_type=TapApplicationType.PYTHON27)
        application.ensure_running()
        return application

    @pytest.mark.bugs("DPNG-11054 [TAP_NG] Response code 409 (name conflict) should be displayed when pushing twice app with the same name")
    def test_cannot_push_application_twice(self, context, sample_app_path, tap_cli, sample_app):
        step("Check that pushing the same application again causes an error")
        with pytest.raises(AssertionError):
            Application.push(context, app_path=sample_app_path, tap_cli=tap_cli, app_type=TapApplicationType.PYTHON27)

    def test_cannot_scale_application_with_incorrect_id(self, api_service_admin_client):
        step("Scale application with incorrect id")
        incorrect_id = "wrong_id"
        expected_message = ApiServiceHttpStatus.MSG_CANNOT_FETCH_INSTANCE.format(incorrect_id)
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, expected_message,
                                                api_service.scale_application, app_id=incorrect_id, replicas=3,
                                                client=api_service_admin_client)

    def test_cannot_scale_application_with_incorrect_instance_number(self, api_service_admin_client):
        step("Scale application with incorrect replicas number")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_INCORRECT_TYPE,
                                                api_service.scale_application, app_id=3, replicas="wrong_number",
                                                client=api_service_admin_client)

    def test_get_application(self, sample_app):
        step("Get application")
        app = Application.get(app_id=sample_app.id)
        step("Check that the apps are the same")
        assert sample_app == app

    def test_change_app_state_in_catalog_and_delete_it(self, context, sample_app_path, tap_cli):
        log_fixture("Push sample application and check it's running")
        application = Application.push(context, app_path=sample_app_path, tap_cli=tap_cli,
                                       app_type=TapApplicationType.PYTHON27)
        application.ensure_running()

        updated_state = TapEntityState.FAILURE
        step("Update app state to {} using catalog api".format(updated_state))
        catalog_api.update_instance(instance_id=self.app.id, field_name="state", value=updated_state)
        step("Check that the app state was updated")
        app = Application.get(app_id=application.id)
        assert app.state == updated_state, "Application is not in the expected state. App state: {}".format(app.state)
        step("Check that the application can be deleted")
        self.app.delete()
        step("Check that application has been removed")
        apps = Application.get_list()
        assert application not in apps
