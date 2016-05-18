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

from modules.constants import ApplicationPath, ServiceCatalogHttpStatus, ServiceLabels, TapComponent as TAP
from modules.markers import priority, components
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceBinding, ServiceInstance
from tests.fixtures import assertions, fixtures


logged_components = (TAP.service_catalog,)
pytestmark = [components.service_catalog]


class TestBindings:

    @pytest.fixture(scope="function")
    def test_app(self, request, test_space, login_to_cf):
        step("Push test app")
        example_app_path = ApplicationPath.SAMPLE_APP
        test_app = Application.push(space_guid=test_space.guid, source_directory=example_app_path)
        assertions.assert_equal_with_retry(True, test_app.cf_api_app_is_running)

        def fin():
            fixtures.delete_or_not_found(test_app.api_delete)
        request.addfinalizer(fin)
        return test_app

    @pytest.fixture(scope="function")
    def test_instance(self, request, test_org, test_space):
        step("Create test instance")
        instance = ServiceInstance.api_create(test_org.guid, test_space.guid, ServiceLabels.MONGO_DB,
                                              service_plan_name="free")

        def fin():
            fixtures.delete_or_not_found(instance.api_delete)
        request.addfinalizer(fin)
        return instance

    @pytest.fixture(scope="function")
    def test_binding(self, request, test_app, test_instance):
        step("Bind test app and test instance")
        test_binding = ServiceBinding.api_create(test_app.guid, test_instance.guid)

        def fin():
            fixtures.delete_or_not_found(test_binding.api_delete)
        request.addfinalizer(fin)
        return test_binding

    @priority.high
    def test_app_bind_unbind_service_instance(self, test_app, test_instance):
        step("Check that test app has no service bindings")
        bindings = ServiceBinding.api_get_list(test_app.guid)
        assert len(bindings) == 0
        step("Bind service instance to app and check")
        test_binding = ServiceBinding.api_create(test_app.guid, test_instance.guid)
        bindings = ServiceBinding.api_get_list(test_app.guid)
        assert test_binding in bindings
        step("Unbind service instance from application and check there are no bindings")
        test_binding.api_delete()
        bindings = ServiceBinding.api_get_list(test_app.guid)
        assert test_binding not in bindings

    @priority.high
    def test_cannot_delete_service_instance_bound_to_app(self, test_app, test_instance, test_binding):
        step("Try to delete service instance")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_BAD_REQUEST,
                                                ServiceCatalogHttpStatus.MSG_BOUND_INSTANCE,
                                                test_instance.api_delete)
        step("Check that the binding was not deleted")
        bindings = ServiceBinding.api_get_list(test_app.guid)
        assert test_binding in bindings

    @priority.medium
    def test_delete_app_with_bound_service(self, test_space, test_app, test_instance, test_binding):
        step("Check that the app can be deleted")
        test_app.api_delete()
        apps = Application.api_get_list(test_space.guid)
        assert test_app not in apps
        step("Check that the instance can be deleted")
        test_instance.api_delete()
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        assert test_instance not in instances


@priority.low
class TestBindingErrors:
    NOT_EXISTING_GUID = "00000000-0000-0000-0000-000000000000"
    INCORRECT_GUID = "incorrect_guid"

    @pytest.fixture(scope="class")
    def test_app(self, request, test_space, login_to_cf):
        step("Push test app")
        example_app_path = ApplicationPath.SAMPLE_APP
        test_app = Application.push(space_guid=test_space.guid, source_directory=example_app_path)
        assertions.assert_equal_with_retry(True, test_app.cf_api_app_is_running)

        def fin():
            fixtures.delete_or_not_found(test_app.api_delete)
        request.addfinalizer(fin)
        return test_app

    @pytest.fixture(scope="class")
    def test_instance(self, request, test_org, test_space):
        step("Create test instance")
        instance = ServiceInstance.api_create(test_org.guid, test_space.guid, ServiceLabels.MONGO_DB,
                                              service_plan_name="free")

        def fin():
            fixtures.delete_or_not_found(instance.api_delete)
        request.addfinalizer(fin)
        return instance

    def test_cannot_bind_not_existing_service_instance(self, test_app):
        step("Try to create service binding to a non-existing service instance")
        expected_error_message = ServiceCatalogHttpStatus.MSG_SERVICE_INST_NOT_FOUND.format(self.NOT_EXISTING_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                ServiceBinding.api_create, test_app.guid, self.NOT_EXISTING_GUID)

    def test_cannot_bind_instance_with_incorrect_guid(self, test_app):
        step("Try to create service binding with an incorrect service instance guid")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_BAD_REQUEST,
                                                ServiceCatalogHttpStatus.MSG_BAD_REQUEST,
                                                ServiceBinding.api_create, test_app.guid, self.INCORRECT_GUID)

    def test_cannot_bind_instance_to_not_existing_app(self, test_instance):
        step("Try to create service binding to a non existing app")
        expected_error_message = ServiceCatalogHttpStatus.MSG_APP_NOT_FOUND.format(self.NOT_EXISTING_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                ServiceBinding.api_create, self.NOT_EXISTING_GUID, test_instance.guid)

    @pytest.mark.bugs("DPNG-6964 http status 500 when creating/deleting service binding by providing incorrect guid")
    def test_cannot_bind_instance_with_incorrect_app_guid(self, test_instance):
        step("Try to create service binding with incorrect app guid")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_BAD_REQUEST,
                                                ServiceCatalogHttpStatus.MSG_BAD_REQUEST,
                                                ServiceBinding.api_create, self.INCORRECT_GUID, test_instance.guid)

    def test_cannot_delete_not_existing_binding(self):
        step("Try to delete non-existing binding")
        test_binding = ServiceBinding(self.NOT_EXISTING_GUID, self.NOT_EXISTING_GUID, self.NOT_EXISTING_GUID)
        expected_error_message = ServiceCatalogHttpStatus.MSG_SERVICE_BINDING_NOT_FOUND.format(self.NOT_EXISTING_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                test_binding.api_delete)

    @pytest.mark.bugs("DPNG-6964 http status 500 when creating/deleting service binding by providing incorrect guid")
    def test_cannot_delete_binding_using_incorrect_binding_guid(self):
        """ DPNG-6964 http status 500 when creating/deleting service binding by providing incorrect guid """
        test_binding = ServiceBinding(self.INCORRECT_GUID, self.INCORRECT_GUID, self.INCORRECT_GUID)
        step("Try to delete service binding by providing incorrect binding guid")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_BAD_REQUEST,
                                                ServiceCatalogHttpStatus.MSG_BAD_REQUEST,
                                                test_binding.api_delete)
