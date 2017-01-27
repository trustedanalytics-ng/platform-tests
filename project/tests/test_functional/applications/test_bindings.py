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
from modules.tap_object_model import Application, ServiceInstance, KubernetesPod
from tests.fixtures import assertions

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
        bindings = sample_python_app.get_bindings()
        assert bindings is None
        step("Bind service instance to app and check")
        sample_python_app.bind(service_instance_id=service_instance.id)
        sample_python_app.ensure_running()
        sample_python_app.ensure_bound(service_instance_id=service_instance.id)
        step("Unbind service instance from application and check there are no bindings")
        sample_python_app.unbind(service_instance_id=service_instance.id)
        sample_python_app.ensure_running()
        sample_python_app.ensure_unbound(service_instance_id=service_instance.id)

    @priority.high
    def test_cannot_delete_service_instance_bound_to_app(self, sample_python_app, service_instance):
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
        step("Bind test app and test instance")
        sample_python_app.bind(service_instance_id=service_instance.id)
        sample_python_app.ensure_running()

        step("Try to delete service instance")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_FORBIDDEN,
                                                ServiceCatalogHttpStatus.MSG_BOUND_INSTANCE.format(
                                                    service_instance.name,
                                                    sample_python_app.name,
                                                    sample_python_app.id
                                                ),
                                                service_instance.delete)
        step("Check that the binding was not deleted")
        sample_python_app.ensure_bound(service_instance_id=service_instance.id)

    @priority.medium
    def test_delete_app_with_bound_service(self, sample_python_app, service_instance):
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

        step("Bind test app and test instance")
        sample_python_app.bind(service_instance_id=service_instance.id)
        sample_python_app.ensure_running()

        step("Check that the app can be deleted")
        sample_python_app.stop()
        sample_python_app.ensure_stopped()
        sample_python_app.delete()
        apps = Application.get_list()
        assert sample_python_app not in apps
        step("Check that the instance can be deleted")
        service_instance.stop()
        service_instance.ensure_stopped()
        service_instance.delete()
        instances = ServiceInstance.get_list()
        assert service_instance not in instances


@pytest.mark.usefixtures("open_tunnel")
@incremental
class TestCreateDeleteBinding:

    @priority.medium
    def test_0_create_binding(self, service_instance, sample_java_app):
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
        2. Wait until app will be runing.
        """

        step("Bind test app and test instance")
        sample_java_app.bind(service_instance_id=service_instance.id)
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
        platform_bindings_list = sample_java_app.get_bindings()
        pod_bindings = KubernetesPod.get_from_tap_app_name(sample_java_app.name).get_bindings()
        assert len(pod_bindings) == len(platform_bindings_list)

    @priority.medium
    def test_2_delete_binding(self, sample_java_app, service_instance):
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
        sample_java_app.unbind(service_instance_id=service_instance.id)
        sample_java_app.ensure_running()
        sample_java_app.ensure_unbound(service_instance_id=service_instance.id)

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
        platform_bindings_list = sample_java_app.get_bindings()
        pod_bindings = KubernetesPod.get_from_tap_app_name(sample_java_app.name).get_bindings()
        assert platform_bindings_list is None
        assert len(pod_bindings) == 0


@priority.low
class TestBindingErrors:

    @pytest.mark.sample_apps_test
    def test_cannot_bind_not_existing_service_instance(self, sample_python_app):
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
                                                sample_python_app.bind, service_instance_id=Guid.NON_EXISTING_GUID)

    @pytest.mark.sample_apps_test
    def test_cannot_bind_instance_with_incorrect_id(self, sample_python_app):
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
            Guid.INVALID_GUID, sample_python_app.id
        )
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                sample_python_app.bind, service_instance_id=Guid.INVALID_GUID)

    def test_cannot_bind_instance_to_not_existing_app(self, service_instance):
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
                                                service_instance.bind, application_id_to_bound=Guid.NON_EXISTING_GUID)

    def test_cannot_bind_instance_with_incorrect_app_id(self, service_instance):
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
                                                service_instance.bind, application_id_to_bound=Guid.INVALID_GUID)
