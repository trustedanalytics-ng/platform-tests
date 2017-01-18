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

from modules.constants import ServiceCatalogHttpStatus, ServiceLabels, ServicePlan, TapComponent as TAP, Guid
from modules.markers import priority, incremental
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Application, Binding, ServiceInstance, KubernetesPod
from tests.fixtures import assertions
from tests.fixtures.context import Context

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


@pytest.fixture(scope="class")
def service_instance(class_context):
    step("Create test instance")
    instance = ServiceInstance.create_with_name(context=class_context, offering_label=ServiceLabels.KAFKA,
                                                plan_name=ServicePlan.SHARED)
    log_fixture("Check the service instance is running")
    instance.ensure_running()
    return instance


class TestBindings:

    @pytest.fixture(scope="function")
    def instance_binding(self, context, sample_python_app, service_instance):
        step("Bind test app and test instance")
        return Binding.create(context=context, app_id=sample_python_app.id,
                              service_instance_id=service_instance.id)

    @pytest.mark.bugs("DPNG-14052 App id in bindings response does not match app id in request")
    @priority.high
    def test_app_bind_unbind_service_instance(self, sample_python_app, service_instance):
        """
        <b>Description:</b>
        Checks if a service instance can be bound/unbound to an application.

        <b>Input data:</b>
        1. Sample python application.
        2. Service instance.

        <b>Expected results:</b>
        Service instance can be bind and unbind.

        <b>Steps:</b>
        1. Verify that the application has no service bindings.
        2. Bind the service instance.
        3. Verify the binding.
        4. Unbound the service instance.
        """
        step("Check that test app has no service bindings")
        bindings = Binding.get_list(app_id=sample_python_app.id)
        assert len(bindings) == 0
        step("Bind service instance to app and check")
        test_binding = Binding.create(context=Context(), app_id=sample_python_app.id,
                                      service_instance_id=service_instance.id)
        bindings = Binding.get_list(app_id=sample_python_app.id)
        assert test_binding in bindings
        step("Unbind service instance from application and check there are no bindings")
        test_binding.delete()
        bindings = Binding.get_list(app_id=sample_python_app.id)
        assert test_binding not in bindings

    @pytest.mark.bugs("DPNG-14052 App id in bindings response does not match app id in request")
    @priority.high
    def test_cannot_delete_service_instance_bound_to_app(self, sample_python_app, service_instance, instance_binding):
        """
        <b>Description:</b>
        Checks if a bound service instance cannot be deleted.

        <b>Input data:</b>
        1. Sample python application.
        2. Service instance.
        3. Binding.

        <b>Expected results:</b>
        Service instance cannot be deleted.

        <b>Steps:</b>
        1. Check if the service instance cannot be deleted.
        2. Verify the binding exists.
        """
        step("Try to delete service instance")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_FORBIDDEN,
                                                ServiceCatalogHttpStatus.MSG_BOUND_INSTANCE.format(
                                                    service_instance.name,
                                                    sample_python_app.name,
                                                    sample_python_app.id
                                                ),
                                                service_instance.delete)
        step("Check that the binding was not deleted")
        bindings = Binding.get_list(app_id=sample_python_app.id)
        assert instance_binding in bindings

    @pytest.mark.bugs("DPNG-14052 App id in bindings response does not match app id in request")
    @priority.medium
    def test_delete_app_with_bound_service(self, sample_python_app, service_instance, instance_binding):
        """
        <b>Description:</b>
        Checks if an application with a bound service can be deleted.

        <b>Input data:</b>
        1. Sample python application.
        2. Service instance.
        3. Binding.

        <b>Expected results:</b>
        The application and the service instance are deleted.

        <b>Steps:</b>
        1. Delete the application.
        2. Verify the application is deleted.
        3. Delete the service instance.
        4. Verify the service instance is deleted.
        """
        step("Check that the app can be deleted")
        sample_python_app.delete()
        apps = Application.get_list()
        assert sample_python_app not in apps
        step("Check that the instance can be deleted")
        service_instance.delete()
        instances = ServiceInstance.get_list()
        assert service_instance not in instances


@pytest.mark.usefixtures("open_tunnel")
@incremental
class TestCreateDeleteBinding:

    @pytest.mark.bugs("DPNG-14906 [TAP-NG] Bad create binding http response.")
    @priority.medium
    def test_0_create_binding(self, class_context, service_instance, sample_java_app):
        """
        <b>Description:</b>
        Checks if a binding can be created.

        <b>Input data:</b>
        1. Sample java application.
        2. Service instance.

        <b>Expected results:</b>
        Binding is made.

        <b>Steps:</b>
        1. Create a binding.
        2. Restart the app.
        """
        self.__class__.binding = Binding.create(context=class_context, app_id=sample_java_app.id,
                                                service_instance_id=service_instance.id)
        step("Restarting the app to update pod environment variables.")
        sample_java_app.restart()
        sample_java_app.ensure_running()

    @priority.medium
    def test_1_compare_bindings_list_with_k8s(self, sample_java_app):
        """
        <b>Description:</b>
        Checks if a TAP bindings and k8s bindings are the same.

        <b>Input data:</b>
        1. Sample java application.

        <b>Expected results:</b>
        Bindings are the same.

        <b>Steps:</b>
        1. Retrieve bindings.
        2. Verify they are the same.
        """
        platform_bindings_list = Binding.get_list(app_id=sample_java_app.id)
        pod_bindings = KubernetesPod.get_from_tap_app_name(sample_java_app.name).get_bindings()
        assert len(pod_bindings) == len(platform_bindings_list) and len(pod_bindings)

    @pytest.mark.bugs("DPNG-14052 App id in bindings response does not match app id in request")
    @priority.medium
    def test_2_delete_binding(self, sample_java_app):
        """
        <b>Description:</b>
        Checks if a binding can be removed.

        <b>Input data:</b>
        1. Binding.
        2. Sample java application

        <b>Expected results:</b>
        Binding is deleted.

        <b>Steps:</b>
        1. Delete binding.
        2. Verify the binding is deleted.
        """
        self.__class__.binding.delete()
        step("Restarting the app to update pod environment variables.")
        sample_java_app.restart()
        sample_java_app.ensure_running()

    @priority.medium
    def test_3_compare_bindings_list_with_k8s(self, sample_java_app):
        """
        <b>Description:</b>
        Checks if a TAP bindings and k8s bindings are the same.

        <b>Input data:</b>
        1. Sample java application.

        <b>Expected results:</b>
        Bindings are the same.

        <b>Steps:</b>
        1. Retrieve bindings.
        2. Verify they are the same.
        """
        platform_bindings_list = Binding.get_list(app_id=sample_java_app.id)
        pod_bindings = KubernetesPod.get_from_tap_app_name(sample_java_app.name).get_bindings()
        assert pod_bindings == platform_bindings_list


@priority.low
class TestBindingErrors:

    @pytest.mark.bugs("DPNG-14052 App id in bindings response does not match app id in request")
    @pytest.mark.sample_apps_test
    def test_cannot_bind_not_existing_service_instance(self, context, sample_python_app):
        """
        <b>Description:</b>
        Checks if a binding cannot be made with not existing service instance.

        <b>Input data:</b>
        1. Sample python application.

        <b>Expected results:</b>
        A binding cannot be made.

        <b>Steps:</b>
        1. Verify making a binding fails.
        """
        step("Try to create service binding to a non-existing service instance")
        expected_error_message = ServiceCatalogHttpStatus.MSG_CANNOT_BOUND_INSTANCE.format(
            Guid.NON_EXISTING_GUID, sample_python_app.id
        )
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                Binding.create, context=context, app_id=sample_python_app.id,
                                                service_instance_id=Guid.NON_EXISTING_GUID)

    @pytest.mark.bugs("DPNG-14052 App id in bindings response does not match app id in request")
    @pytest.mark.sample_apps_test
    def test_cannot_bind_instance_with_incorrect_id(self, context, sample_python_app):
        """
        <b>Description:</b>
        Checks if a binding cannot be made with incorrect id.

        <b>Input data:</b>
        1. Sample python application.

        <b>Expected results:</b>
        A binding cannot be made.

        <b>Steps:</b>
        1. Verify making a binding fails.
        """
        step("Try to create service binding with an incorrect service instance guid")
        expected_error_message = ServiceCatalogHttpStatus.MSG_CANNOT_BOUND_INSTANCE.format(
            Guid.NON_EXISTING_GUID, sample_python_app.id
        )
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                Binding.create, context=context, app_id=sample_python_app.id,
                                                service_instance_id=Guid.INVALID_GUID)

    def test_cannot_bind_instance_to_not_existing_app(self, context, service_instance):
        """
        <b>Description:</b>
        Checks if a binding cannot be made with not existing application.

        <b>Input data:</b>
        1. Service instance.

        <b>Expected results:</b>
        A binding cannot be made.

        <b>Steps:</b>
        1. Verify making a binding fails.
        """
        step("Try to create service binding to a non existing app")
        expected_error_message = ServiceCatalogHttpStatus.MSG_APP_NOT_FOUND.format(Guid.NON_EXISTING_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                Binding.create, context=context, app_id=Guid.NON_EXISTING_GUID,
                                                service_instance_id=service_instance.id)

    def test_cannot_bind_instance_with_incorrect_app_id(self, context, service_instance):
        """
        <b>Description:</b>
        Checks if a binding cannot be made with incorrect application id.

        <b>Input data:</b>
        1. Service instance.

        <b>Expected results:</b>
        A binding cannot be made.

        <b>Steps:</b>
        1. Verify making a binding fails.
        """
        step("Try to create service binding with incorrect app id")
        expected_error_message = ServiceCatalogHttpStatus.MSG_APP_NOT_FOUND.format(Guid.INVALID_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND,
                                                expected_error_message,
                                                Binding.create, context=context, app_id=Guid.INVALID_GUID,
                                                service_instance_id=service_instance.id)

    @pytest.mark.bugs("DPNG-15127 [api-tests] Fixture instance_binding fails with unrecoverable error")
    def test_cannot_delete_not_existing_binding(self):
        """
        <b>Description:</b>
        Checks if a not existing binding cannot be deleted.

        <b>Input data:</b>

        <b>Expected results:</b>
        A binding cannot be deleted.

        <b>Steps:</b>
        1. Verify deleting a binding fails.
        """
        step("Try to delete non-existing binding")
        test_binding = Binding(app_id=Guid.NON_EXISTING_GUID, service_instance_id=Guid.NON_EXISTING_GUID)
        expected_error_message = ServiceCatalogHttpStatus.MSG_APP_NOT_FOUND.format(Guid.NON_EXISTING_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                test_binding.delete)

    @pytest.mark.bugs("DPNG-15127 [api-tests] Fixture instance_binding fails with unrecoverable error")
    def test_cannot_delete_binding_using_incorrect_binding_id(self):
        """
        <b>Description:</b>
        Checks if a binding cannot be deleted with incorrect binding id.

        <b>Input data:</b>

        <b>Expected results:</b>
        A binding cannot be deleted.

        <b>Steps:</b>
        1. Verify deleting a binding fails.
        """
        test_binding = Binding(app_id=Guid.INVALID_GUID, service_instance_id=Guid.INVALID_GUID)
        step("Try to delete service binding by providing incorrect binding id")
        expected_error_message = ServiceCatalogHttpStatus.MSG_APP_NOT_FOUND.format(Guid.INVALID_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND,
                                                expected_error_message,
                                                test_binding.delete)
