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

from modules.constants import ApiServiceHttpStatus, CatalogHttpStatus, TapApplicationType, ServiceLabels, \
    ServicePlan, TapEntityState, TapComponent as TAP
from modules.exceptions import UnexpectedResponseError
from modules.http_calls.platform import api_service, catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Application, CatalogApplicationInstance, ServiceInstance
from modules.tap_object_model.prep_app import PrepApp
from modules.test_names import generate_test_object_name
from tests.fixtures import assertions


logged_components = (TAP.api_service, TAP.catalog)


@pytest.mark.usefixtures("open_tunnel")
class TestApiServiceApplication:
    EXPECTED_MESSAGE_WHEN_APP_PUSHED_TWICE = "Bad response status: 409"
    APPLICATION_INVALID_ID = generate_test_object_name(short=True)
    SERVICE_INVALID_ID = generate_test_object_name(short=True)

    @pytest.fixture(scope="class")
    def sample_app(self, class_context, test_sample_apps, api_service_admin_client):
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(test_sample_apps.tapng_python_app.filepath)
        manifest_params = {"type" : TapApplicationType.PYTHON27}
        manifest_path = p_a.update_manifest(params=manifest_params)

        log_fixture("Push sample application")
        application = Application.push(class_context, app_path=test_sample_apps.tapng_python_app.filepath,
                                       name=p_a.app_name, manifest_path=manifest_path,
                                       client=api_service_admin_client)
        application.ensure_running()
        return application

    @pytest.fixture(scope="class")
    def service_instance(self, class_context):
        log_fixture("Create sample service instance")
        instance = ServiceInstance.create_with_name(class_context, offering_label=ServiceLabels.RABBIT_MQ,
                                                    plan_name=ServicePlan.SINGLE_SMALL)
        step("Ensure that instance is running")
        instance.ensure_running()
        return instance

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_push_application_twice(self, context, test_sample_apps, sample_app,
                                           api_service_admin_client):
        """
        <b>Description:</b>
        Tries to push the same application twice

        <b>Input data:</b>
        - Sample application that will be pushed twice

        <b>Expected results:</b>
        - The second push is not possible

        <b>Steps:</b>
        - Application is pushed
        - Application is pushed again in the test itself
        - The second push is blocked
        """
        step("Check that pushing the same application again causes an error")
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(test_sample_apps.tapng_python_app.filepath)
        manifest_params = {"type" : TapApplicationType.PYTHON27,
                           "name": sample_app.name}
        manifest_path = p_a.update_manifest(params=manifest_params)

        with pytest.raises(UnexpectedResponseError) as e:
            Application.push(context, app_path=test_sample_apps.tapng_python_app.filepath,
                             name=sample_app.name, manifest_path=manifest_path,
                             client=api_service_admin_client)
        assert self.EXPECTED_MESSAGE_WHEN_APP_PUSHED_TWICE in str(e)

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_scale_application_with_incorrect_id(self, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to scale application that doesn't exist

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        - It's not possible to scale non-existent application

        <b>Steps:</b>
        - Scale the application that has incorrect id

        """
        step("Scale application with incorrect id")
        incorrect_id = "wrong_id"
        expected_message = ApiServiceHttpStatus.MSG_CANNOT_FETCH_APP_INSTANCE.format(incorrect_id)
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, expected_message,
                                                api_service.scale_application, app_id=incorrect_id, replicas=3,
                                                client=api_service_admin_client)

    def test_cannot_restart_with_incorrect_id(self, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to restart application that does not exist

        <b>Input data:</b>
        - Admin credentials

        <b>Expected results:</b>
        It's not possible to restart non-existent application

        <b>Steps:</b>
        - Restart the non-existent application
        """
        step("Restart application with incorrect id")
        incorrect_id = "wrong_id"
        expected_message = ApiServiceHttpStatus.MSG_CANNOT_FETCH_APP_INSTANCE.format(incorrect_id)
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND, expected_message,
                                                api_service.restart_application, app_id=incorrect_id,
                                                client=api_service_admin_client)

    @pytest.mark.bugs("DPNG-14865 Adjust response msg in test_cannot_scale_application_with_negative_instances_number")
    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_scale_application_with_incorrect_instances_number(self, sample_app, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to scale the application with bad data

        <b>Input data:</b>
        - Sample application
        - Admin credentials

        <b>Expected results:</b>
        - It's not possible to scale application with bad data

        <b>Steps:</b>
        - Download the application and push it to platform
        - Scale the app by providing bad amount of replicas
        """
        step("Scale application with incorrect replicas number")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_INCORRECT_TYPE,
                                                api_service.scale_application, app_id=sample_app.id,
                                                replicas="wrong_number", client=api_service_admin_client)

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_cannot_scale_application_with_negative_instances_number(self, sample_app, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to scale the application with negative instances number

        <b>Input data:</b>
        - Sample application
        - Admin credentials

        <b>Expected results:</b>
        - It's not possible to scale application with negative instances number

        <b>Steps:</b>
        - Download the application and push it to platform
        - Scale the app by providing negative amount of replicas
        """
        step("Scale application with negative replicas number")
        expected_message = ApiServiceHttpStatus.MSG_MINIMUM_ALLOWED_REPLICA
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST, expected_message,
                                                sample_app.scale, replicas=-1, client=api_service_admin_client)

    def test_cannot_push_application_with_invalid_name(self, context, sample_app,
                                                       test_sample_apps,
                                                       api_service_admin_client):
        """
        <b>Description:</b>
        Tries to push the application with invalid name

        <b>Input data:</b>
        - Sample application that was already pushed
        - Admin credentials

        <b>Expected results:</b>
        - Pushing the application with invalid name is forbidden

        <b>Steps:</b>
        - Application is pushed
        - Application is prepared again and it's name is changed to invalid
        - Application with the changed name is pushed
        """
        step("Change the application name to invalid")
        p_a = PrepApp(test_sample_apps.tapng_python_app.filepath)
        app_name = "invalid_-application-_name"
        manifest_params = {"type" : TapApplicationType.PYTHON27,
                           "name": app_name}
        manifest_path = p_a.update_manifest(params=manifest_params)

        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(app_name, app_name),
                                                Application.push, context,
                                                app_path=test_sample_apps.tapng_python_app.filepath,
                                                name=app_name, manifest_path=manifest_path,
                                                client=api_service_admin_client)

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_restart_application(self, sample_app):
        """
        <b>Description:</b>
        Restarts the application

        <b>Input data:</b>
        - Application that was already pushed to platform

        <b>Expected results:</b>
        - It's possible to restart the application and the application will
          be running after such procedure

        <b>Steps:</b>
        - Download sample app
        - Push the sample app
        - Make sure the application is running
        - Restart the application
        - Verify that application is running
        """
        step("Make sure the application is running so we can restart it")
        sample_app.ensure_running()
        step("Restart application")
        sample_app.restart()
        step("Verify the application is running")
        sample_app.ensure_running()

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_get_application(self, sample_app, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to retrieve the application by its id

        <b>Input data:</b>
        - Pushed sample application
        - Admin credentials

        <b>Expected results:</b>
        It's possible to retrieve the application by id

        <b>Steps:</b>
        - Pushed the sample app
        - Make sure the application has received id
        - Retrieve the application by it's id
        - Compare the application that was pushed and received by id
        """
        step("Make sure the sample app has updated id")
        sample_app._ensure_has_id()
        step("Get application")
        app = Application.get(app_inst_id=sample_app.id, client=api_service_admin_client)
        step("Check that the apps are the same")
        assert sample_app == app

    @priority.low
    @pytest.mark.components(TAP.api_service)
    def test_scale_application_with_zero_instances_number(self, sample_app, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to scale the application with zero instances number

        <b>Input data:</b>
        - Sample application
        - Admin credentials

        <b>Expected results:</b>
        - After scaling the application down to zero, it should stop

        <b>Steps:</b>
        - Download the application and push it to platform
        - Scale the app by providing zero amount of replicas
        - Make sure the application has stopped
        - Verify the number of replication and running instances
        """
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
    def test_change_app_state_in_catalog_and_delete_it(self, context, test_sample_apps, api_service_admin_client):
        """
        <b>Description:</b>
        Change the application state in catalog and later delete it

        <b>Input data:</b>
        - Path to application
        - Admin credentials

        <b>Expected results:</b>
        - Application state can be changed in catalog
        - Application state can be set back via api service

        <b>Steps:</b>
        - Prepare the application and push it
        - Make sure the application is running
        - Change the state of the application via catalog
        - Make sure the state has changed
        - Stop the application via api service client and remove it
        - Verify the application was removed
        """
        log_fixture("sample_application: update manifest")
        p_a = PrepApp(test_sample_apps.tapng_python_app.filepath)
        manifest_params = {"type" : TapApplicationType.PYTHON27}
        manifest_path = p_a.update_manifest(params=manifest_params)

        log_fixture("Push sample application and check it's running")
        application = Application.push(context, app_path=test_sample_apps.tapng_python_app.filepath,
                                       name=p_a.app_name, manifest_path=manifest_path,
                                       client=api_service_admin_client)
        application.ensure_running()

        step("Check that the application has only one instance")
        instances = CatalogApplicationInstance.get_list_for_application(application_id=application.id)
        assert len(instances) == 1
        updated_state = TapEntityState.FAILURE
        step("Update app state to {} using catalog api".format(updated_state))
        catalog_api.update_instance(instance_id=instances[0].id, field_name="state", value=updated_state)
        step("Check that the app state was updated")
        app = Application.get(app_inst_id=application.id, client=api_service_admin_client)
        assert app.state == updated_state, "Application is not in the expected state. App state: {}".format(app.state)
        step("Check that the application can be deleted")
        application.delete()
        step("Check that application has been removed")
        apps = Application.get_list(client=api_service_admin_client)
        assert application not in apps

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_bind_invalid_ids(self, sample_java_app, service_instance, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to bind the application and service with invalid ids.

        <b>Input data:</b>
        - Sample application that was already pushed
        - Sample service that was already pushed
        - Admin credentials

        <b>Expected results:</b>
        - Binding application and service with invalid ids is not possible.

        <b>Steps:</b>
        - Application is pushed
        - Service is pushed
        - Try to bind application to service with invalid application id
        - Verify that HTTP response status code is 404 with proper message.
        - Try to bind service to application with invalid service id
        - Verify that HTTP response status code is 404 with proper message.
        - Try to bind application and service to service with invalid application and service ids
        - Verify that HTTP response status code is 404 with proper message.
        - Try to bind application to service with empty application id
        - Verify that HTTP response status code is 400 with proper message.
        - Try to bind service to service with empty service id
        - Verify that HTTP response status code is 400 with proper message.
        """
        assert sample_java_app.bindings is None
        assert service_instance.bindings == []

        step("Bind invalid application to service")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_APP_NOT_FOUND.
                                                format(self.APPLICATION_INVALID_ID, self.APPLICATION_INVALID_ID),
                                                service_instance.bind,
                                                application_id_to_bound=self.APPLICATION_INVALID_ID,
                                                client=api_service_admin_client)
        step("Verify there are no bindings in service")
        assert service_instance.bindings == []

        step("Bind invalid service to application")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_SERVICE_NOT_FOUND,
                                                sample_java_app.bind, service_instance_id=self.SERVICE_INVALID_ID,
                                                client=api_service_admin_client)
        step("Verify there are no bindings in application")
        assert sample_java_app.bindings is None

        step("Bind invalid application and service to service")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_ONLY_ONE_ID_EXPECTED.
                                                format(self.APPLICATION_INVALID_ID, self.APPLICATION_INVALID_ID),
                                                service_instance.bind,
                                                application_id_to_bound=self.APPLICATION_INVALID_ID,
                                                service_id_to_bound=self.SERVICE_INVALID_ID,
                                                client=api_service_admin_client)
        step("Verify there are no bindings in service")
        assert service_instance.bindings == []

        step("Bind application to service with empty id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_ONLY_ONE_ID_EXPECTED.
                                                format("", service_instance.id),
                                                service_instance.bind,
                                                application_id_to_bound="",
                                                client=api_service_admin_client)
        step("Verify there are no bindings in service")
        assert service_instance.bindings == []

        step("Bind service to service with empty id")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_BAD_REQUEST,
                                                ApiServiceHttpStatus.MSG_ONLY_ONE_ID_EXPECTED.
                                                format("", service_instance.id),
                                                service_instance.bind,
                                                service_id_to_bound="",
                                                client=api_service_admin_client)
        step("Verify there are no bindings in service")
        assert service_instance.bindings == []

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_unbind_invalid_ids(self, sample_java_app, service_instance, api_service_admin_client):
        """
        <b>Description:</b>
        Tries to unbind the application and service with invalid ids.

        <b>Input data:</b>
        - Sample application that was already pushed
        - Sample service that was already pushed
        - Admin credentials

        <b>Expected results:</b>
        - Unbinding application and service with invalid ids is not possible.

        <b>Steps:</b>
        - Application is pushed
        - Service is pushed
        - Try to unbind application from service with invalid application id
        - Verify that HTTP response status code is 404 with proper message.
        - Try to unbind service to application with invalid service id
        - Verify that HTTP response status code is 404 with proper message.
        """
        assert sample_java_app.bindings is None
        assert service_instance.bindings == []

        step("Try to remove non-existent application binding from service")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_APP_NOT_FOUND.
                                                format(self.APPLICATION_INVALID_ID, self.APPLICATION_INVALID_ID),
                                                service_instance.unbind_app, application_id=self.APPLICATION_INVALID_ID,
                                                client=api_service_admin_client)

        step("Try to remove non-existent service binding from application")
        assertions.assert_raises_http_exception(ApiServiceHttpStatus.CODE_NOT_FOUND,
                                                ApiServiceHttpStatus.MSG_SERVICE_NOT_FOUND,
                                                sample_java_app.unbind, service_instance_id=self.SERVICE_INVALID_ID,
                                                client=api_service_admin_client)

    def app_ensure_bound(self, sample_java_app, service_instance, api_service_admin_client):
        sample_java_app.ensure_bound(service_instance.id, client=api_service_admin_client)
        step("Verify there is a single binding in application")
        app_bindings = sample_java_app.get_bindings(client=api_service_admin_client)
        assert len(app_bindings) == 1
        assert app_bindings[0]["entity"]["service_instance_guid"] == service_instance.id
        assert app_bindings[0]["entity"]["service_instance_name"] == service_instance.name
        step("Verify there are no bindings in service")
        assert service_instance.bindings == []

    def svc_ensure_bound(self, sample_java_app, service_instance, api_service_admin_client):
        service_instance.ensure_bound(sample_java_app.id, client=api_service_admin_client)
        step("Verify there is a binding for service")
        svc_bindings = service_instance.get_bindings(client=api_service_admin_client)
        assert len(svc_bindings) == 1
        step("Verify there is a single binding in application")
        app_bindings = sample_java_app.get_bindings(client=api_service_admin_client)
        assert len(app_bindings) == 1
        assert app_bindings[0]["entity"]["service_instance_guid"] == service_instance.id
        assert app_bindings[0]["entity"]["service_instance_name"] == service_instance.name

    def check_bindings(self, sample_java_app, service_instance, api_service_admin_client):
        step("Check whether bindings sections is available in application")
        app = Application.get(sample_java_app.id, client=api_service_admin_client)
        assert len(app.bindings) == 1
        step("Check whether bindings section is available in service")
        svc = ServiceInstance.get(service_id=service_instance.id, client=api_service_admin_client)
        assert len(svc.bindings) == 1

    def svc_ensure_unbound(self, sample_java_app, service_instance, api_service_admin_client):
        service_instance.ensure_unbound(sample_java_app.id, client=api_service_admin_client)
        svc_bindings = service_instance.get_bindings(client=api_service_admin_client)
        assert svc_bindings is None

    def app_ensure_unbound(self, sample_java_app, service_instance, api_service_admin_client):
        sample_java_app.ensure_unbound(service_instance.id, client=api_service_admin_client)
        app_bindings = sample_java_app.get_bindings(client=api_service_admin_client)
        assert app_bindings is None

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_bind_unbind_application_to_service(self, sample_java_app, service_instance, api_service_admin_client):
        """
        <b>Description:</b>
        Bind and unbind the application and service.

        <b>Input data:</b>
        - Sample application that was already pushed
        - Sample service that was already pushed
        - Admin credentials

        <b>Expected results:</b>
        - Binding and unbinding application and service is possible.

        <b>Steps:</b>
        - Application is pushed
        - Service is pushed
        - Bind service to application
        - Verify the application is running
        - Verify service instance is running
        - Verify there is a single binding in application
        - Verify there are no bindings in service

        - Bind application to service
        - Verify the application is running
        - Verify service instance is running
        - Verify there is a binding for service
        - Verify there is a single binding in application

        - Try to remove application bindings from service instance
        - Verify the application is running
        - Verify service instance is running
        - Verify the service has no bindings

        - Try to remove service bindings from application instance
        - Verify the application is running
        - Verify service instance is running
        - Verify the application has no bindings
        """
        if sample_java_app.is_stopped:
            sample_java_app.start()
            sample_java_app.ensure_running()
        if service_instance.is_stopped:
            service_instance.start()
            service_instance.ensure_running()

        step("Bind service to application")
        sample_java_app.bind(service_instance_id=service_instance.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is running")
        service_instance.ensure_running()

        self.app_ensure_bound(sample_java_app, service_instance, api_service_admin_client)

        step("Bind application to service")
        service_instance.bind(application_id_to_bound=sample_java_app.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is running")
        service_instance.ensure_running()

        self.svc_ensure_bound(sample_java_app, service_instance, api_service_admin_client)

        step("Check whether bindings sections is available")
        self.check_bindings(sample_java_app, service_instance, api_service_admin_client)

        step("Try to remove application bindings from service instance")
        service_instance.unbind_app(application_id=sample_java_app.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is running")
        service_instance.ensure_running()
        step("Verify the service has no bindings")
        self.svc_ensure_unbound(sample_java_app, service_instance, api_service_admin_client)

        step("Try to remove service bindings from application instance")
        sample_java_app.unbind(service_instance_id=service_instance.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is running")
        service_instance.ensure_running()
        step("Verify the application has no bindings")
        self.app_ensure_unbound(sample_java_app, service_instance, api_service_admin_client)

    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_bind_unbind_stopped_application_to_service(self, sample_java_app, service_instance,
                                                        api_service_admin_client):
        """
        <b>Description:</b>
        Bind and unbind the application and service.

        <b>Input data:</b>
        - Sample application that was already pushed (in STOPPED state)
        - Sample service that was already pushed
        - Admin credentials

        <b>Expected results:</b>
        - Binding and unbinding application and service is possible.

        <b>Steps:</b>
        - Application is pushed
        - Service is pushed
        - Bind service to application
        - Verify the application is stopped
        - Verify service instance is running
        - Verify there is a single binding in application
        - Verify there are no bindings in service

        - Bind application to service
        - Verify the application is stopped
        - Verify service instance is running
        - Verify there is a binding for service
        - Verify there is a single binding in application

        - Try to remove application bindings from service instance
        - Verify the application is stopped
        - Verify service instance is running
        - Verify the service has no bindings

        - Try to remove service bindings from application instance
        - Verify the application is stopped
        - Verify service instance is running
        - Verify the application has no bindings
        """
        if sample_java_app.is_running:
            sample_java_app.stop()
            sample_java_app.ensure_stopped()
        if service_instance.is_stopped:
            service_instance.start()
            service_instance.ensure_running()

        step("Bind service to application")
        sample_java_app.bind(service_instance_id=service_instance.id, client=api_service_admin_client)
        step("Verify the application is stopped")
        sample_java_app.ensure_stopped()
        step("Verify service instance is running")
        service_instance.ensure_running()

        self.app_ensure_bound(sample_java_app, service_instance, api_service_admin_client)

        step("Bind application to service")
        service_instance.bind(application_id_to_bound=sample_java_app.id, client=api_service_admin_client)
        step("Verify the application is stopped")
        sample_java_app.ensure_stopped()
        step("Verify service instance is running")
        service_instance.ensure_running()

        self.svc_ensure_bound(sample_java_app, service_instance, api_service_admin_client)

        step("Check whether bindings sections is available")
        self.check_bindings(sample_java_app, service_instance, api_service_admin_client)

        step("Try to remove application bindings from service instance")
        service_instance.unbind_app(application_id=sample_java_app.id, client=api_service_admin_client)
        step("Verify the application is stopped")
        sample_java_app.ensure_stopped()
        step("Verify service instance is running")
        service_instance.ensure_running()
        step("Verify the service has no bindings")
        self.svc_ensure_unbound(sample_java_app, service_instance, api_service_admin_client)

        step("Try to remove service bindings from application instance")
        sample_java_app.unbind(service_instance_id=service_instance.id, client=api_service_admin_client)
        step("Verify the application is stopped")
        sample_java_app.ensure_stopped()
        step("Verify service instance is running")
        service_instance.ensure_running()
        step("Verify the application has no bindings")
        self.app_ensure_unbound(sample_java_app, service_instance, api_service_admin_client)


    @priority.high
    @pytest.mark.components(TAP.api_service)
    def test_bind_unbind_application_to_stopped_service(self, sample_java_app, service_instance,
                                                        api_service_admin_client):
        """
        <b>Description:</b>
        Bind and unbind the application and service.

        <b>Input data:</b>
        - Sample application that was already pushed
        - Sample service that was already pushed (in STOPPED state)
        - Admin credentials

        <b>Expected results:</b>
        - Binding and unbinding application and service is possible.

        <b>Steps:</b>
        - Application is pushed
        - Service is pushed
        - Bind service to application
        - Verify the application is running
        - Verify service instance is stopped
        - Verify there is a single binding in application
        - Verify there are no bindings in service

        - Bind application to service
        - Verify the application is running
        - Verify service instance is running
        - Verify there is a binding for service
        - Verify there is a single binding in application

        - Try to remove application bindings from service instance
        - Verify the application is running
        - Verify service instance is running
        - Verify the service has no bindings

        - Try to remove service bindings from application instance
        - Verify the application is running
        - Verify service instance is running
        - Verify the application has no bindings
        """
        if sample_java_app.is_stopped:
            sample_java_app.start()
            sample_java_app.ensure_running()
        if service_instance.is_running:
            service_instance.stop()
            service_instance.ensure_stopped()

        step("Bind service to application")
        sample_java_app.bind(service_instance_id=service_instance.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is stopped")
        service_instance.ensure_stopped()

        self.app_ensure_bound(sample_java_app, service_instance, api_service_admin_client)

        step("Bind application to service")
        service_instance.bind(application_id_to_bound=sample_java_app.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is stopped")
        service_instance.ensure_stopped()

        self.svc_ensure_bound(sample_java_app, service_instance, api_service_admin_client)

        step("Check whether bindings sections is available")
        self.check_bindings(sample_java_app, service_instance, api_service_admin_client)

        step("Try to remove application bindings from service instance")
        service_instance.unbind_app(application_id=sample_java_app.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is stopped")
        service_instance.ensure_stopped()
        step("Verify the service has no bindings")
        self.svc_ensure_unbound(sample_java_app, service_instance, api_service_admin_client)

        step("Try to remove service bindings from application instance")
        sample_java_app.unbind(service_instance_id=service_instance.id, client=api_service_admin_client)
        step("Verify the application is running")
        sample_java_app.ensure_running()
        step("Verify service instance is stopped")
        service_instance.ensure_stopped()
        step("Verify the application has no bindings")
        self.app_ensure_unbound(sample_java_app, service_instance, api_service_admin_client)
