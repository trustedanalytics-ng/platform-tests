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

from modules.constants import ApiServiceHttpStatus, CatalogHttpStatus, TapApplicationType, Urls, TapEntityState, TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.http_calls.platform import api_service, catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Application
from modules.tap_object_model.prep_app import PrepApp
from tests.fixtures import assertions


logged_components = (TAP.api_service, TAP.catalog)


@pytest.mark.bugs("DPNG-11701 After some time it's not possible to push application")
class TestApiServiceApplication:
    SAMPLE_APP_URL = Urls.tapng_python_app_url
    EXPECTED_MESSAGE_WHEN_APP_PUSHED_TWICE = "Bad response status: 409"
    APP_WITH_INVALID_NAME_MSG = "Message with invalid name"

    @pytest.fixture(scope="class")
    def sample_app(self, class_context, sample_app_path, api_service_admin_client):
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(sample_app_path)
        manifest_params = {"type" : TapApplicationType.PYTHON27}
        manifest_path = p_a.update_manifest(params=manifest_params)

        log_fixture("Push sample application")
        application = Application.push(class_context, app_path=sample_app_path,
                                       name=p_a.app_name, manifest_path=manifest_path,
                                       client=api_service_admin_client)
        application.ensure_running()
        return application

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_push_application_twice(self, context, sample_app_path, sample_app,
                                           api_service_admin_client):
        step("Check that pushing the same application again causes an error")
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(sample_app_path)
        manifest_params = {"type" : TapApplicationType.PYTHON27,
                           "name": sample_app.name}
        manifest_path = p_a.update_manifest(params=manifest_params)

        with pytest.raises(UnexpectedResponseError) as e:
            Application.push(context, app_path=sample_app_path,
                             name=sample_app.name, manifest_path=manifest_path,
                             client=api_service_admin_client)
        assert self.EXPECTED_MESSAGE_WHEN_APP_PUSHED_TWICE in str(e)

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_scale_application_with_incorrect_id(self, api_service_admin_client):
        step("Scale application with incorrect id")
        incorrect_id = "wrong_id"
        expected_message = ApiServiceHttpStatus.MSG_CANNOT_FETCH_APP_INSTANCE.format(incorrect_id)
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, expected_message,
                                                api_service.scale_application, app_id=incorrect_id, replicas=3,
                                                client=api_service_admin_client)

    def test_cannot_restart_with_incorrect_id(self, api_service_admin_client):
        """Attempts to restart non existent applicatin id"""
        step("Restart application with incorrect id")
        incorrect_id = "wrong_id"
        expected_message = ApiServiceHttpStatus.MSG_CANNOT_FETCH_APP_INSTANCE.format(incorrect_id)
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, expected_message,
                                                api_service.restart_application, app_id=incorrect_id,
                                                client=api_service_admin_client)

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_scale_application_with_incorrect_instances_number(self, sample_app, api_service_admin_client):
        step("Scale application with incorrect replicas number")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_INCORRECT_TYPE,
                                                api_service.scale_application, app_id=sample_app.id,
                                                replicas="wrong_number", client=api_service_admin_client)

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_scale_application_with_negative_instances_number(self, sample_app, api_service_admin_client):
        step("Scale application with negative replicas number")
        expected_message = ApiServiceHttpStatus.MSG_MINIMUM_ALLOWED_REPLICA
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST, expected_message,
                                                sample_app.scale, replicas=-1, client=api_service_admin_client)

    def test_cannot_push_application_with_invalid_name(self, context, sample_app,
                                                       sample_app_path,
                                                       api_service_admin_client):
        step("Change the application name to invalid")
        p_a = PrepApp(sample_app_path)
        app_name = "invalid_-application-_name"
        manifest_params = {"type" : TapApplicationType.PYTHON27,
                           "name": app_name}
        manifest_path = p_a.update_manifest(params=manifest_params)

        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(app_name),
                                                Application.push, context, app_path=sample_app_path,
                                                name=sample_app.name, manifest_path=manifest_path,
                                                client=api_service_admin_client)

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_restart_application(self, sample_app):
        """Attempts to restart an application and verifies it's running"""
        step("Make sure the application is running so we can restart it")
        sample_app.ensure_running()
        step("Restart application")
        sample_app.restart()
        step("Verify the application is running")
        sample_app.ensure_running()

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_get_application(self, sample_app, api_service_admin_client):
        step("Make sure the sample app has updated id")
        sample_app._ensure_has_id()
        step("Get application")
        app = Application.get(app_inst_id=sample_app.id, client=api_service_admin_client)
        step("Check that the apps are the same")
        assert sample_app == app

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_scale_application_with_zero_instances_number(self, sample_app, api_service_admin_client):
        step("Scale application with zero replicas number")
        replicas_number = 0
        sample_app.scale(replicas=replicas_number, client=api_service_admin_client)
        step("Check that application is stopped, there are zero replicas and there are no running instances")
        app = Application.get(app_inst_id=sample_app.id, client=api_service_admin_client)
        app.ensure_stopped()
        assert app.replication == replicas_number, "Application does not have expected number of replication. App " \
                                                   "replicas number: {}".format(app.replication)
        assert app.running_instances == replicas_number, "Application does not have expected number of running " \
                                                         "instances. App running instances number: {}"\
                                                         .format(app.running_instances)

    @priority.medium
    @pytest.mark.components(TAP.api_service, TAP.catalog)
    def test_change_app_state_in_catalog_and_delete_it(self, context, sample_app_path,
                                                       api_service_admin_client):
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(sample_app_path)
        manifest_params = {"type" : TapApplicationType.PYTHON27}
        manifest_path = p_a.update_manifest(params=manifest_params)

        log_fixture("Push sample application and check it's running")
        application = Application.push(context, app_path=sample_app_path,
                                       name=p_a.app_name, manifest_path=manifest_path,
                                       client=api_service_admin_client)
        application.ensure_running()

        updated_state = TapEntityState.FAILURE
        step("Update app state to {} using catalog api".format(updated_state))
        catalog_api.update_instance(instance_id=application.id, field_name="state", value=updated_state)
        step("Check that the app state was updated")
        app = Application.get(app_inst_id=application.id, client=api_service_admin_client)
        assert app.state == updated_state, "Application is not in the expected state. App state: {}".format(app.state)
        step("Stop application")
        app.stop()
        app.ensure_stopped()
        step("Check that the application can be deleted")
        application.delete()
        step("Check that application has been removed")
        apps = Application.get_list(client=api_service_admin_client)
        assert application not in apps
