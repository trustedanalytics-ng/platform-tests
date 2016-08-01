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

from modules.constants import ServiceCatalogHttpStatus, ServiceLabels, ServicePlan, TapComponent as TAP
from modules.http_calls import cloud_foundry as cf
from modules.markers import priority, incremental
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceBinding, ServiceInstance
from tests.fixtures import assertions, fixtures


logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


@pytest.fixture(scope="class")
def test_instance(class_context, request, test_org, test_space):
    step("Create test instance")
    instance = ServiceInstance.api_create_with_plan_name(context=class_context, org_guid=test_org.guid,
                                                         space_guid=test_space.guid,
                                                         service_label=ServiceLabels.MONGO_DB,
                                                         service_plan_name=ServicePlan.FREE)

    return instance


class TestBindings:

    @pytest.fixture(scope="function")
    def test_binding(self, request, sample_python_app, test_instance):
        step("Bind test app and test instance")
        test_binding = ServiceBinding.api_create(sample_python_app.guid, test_instance.guid)

        def fin():
            fixtures.delete_or_not_found(test_binding.cleanup)
        request.addfinalizer(fin)
        return test_binding

    @priority.high
    def test_app_bind_unbind_service_instance(self, sample_python_app, test_instance):
        step("Check that test app has no service bindings")
        bindings = ServiceBinding.api_get_list(sample_python_app.guid)
        assert len(bindings) == 0
        step("Bind service instance to app and check")
        test_binding = ServiceBinding.api_create(sample_python_app.guid, test_instance.guid)
        bindings = ServiceBinding.api_get_list(sample_python_app.guid)
        assert test_binding in bindings
        step("Unbind service instance from application and check there are no bindings")
        test_binding.api_delete()
        bindings = ServiceBinding.api_get_list(sample_python_app.guid)
        assert test_binding not in bindings

    @priority.high
    def test_cannot_delete_service_instance_bound_to_app(self, sample_python_app, test_instance, test_binding):
        step("Try to delete service instance")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_BAD_REQUEST,
                                                ServiceCatalogHttpStatus.MSG_BOUND_INSTANCE,
                                                test_instance.api_delete)
        step("Check that the binding was not deleted")
        bindings = ServiceBinding.api_get_list(sample_python_app.guid)
        assert test_binding in bindings

    @priority.medium
    @pytest.mark.usefixtures("test_binding")
    def test_delete_app_with_bound_service(self, test_space, sample_python_app, test_instance):
        step("Check that the app can be deleted")
        sample_python_app.api_delete()
        apps = Application.api_get_list(test_space.guid)
        assert sample_python_app not in apps
        step("Check that the instance can be deleted")
        test_instance.api_delete()
        instances = ServiceInstance.api_get_list(space_guid=test_space.guid)
        assert test_instance not in instances


@incremental
class TestCreateDeleteBinding:

    @priority.medium
    def test_0_create_binding(self, test_instance, sample_java_app):
        self.__class__.binding = ServiceBinding.api_create(sample_java_app.guid, test_instance.guid)
        bindings = sample_java_app.cf_api_get_summary()['service_names']
        assert list((test_instance.name,)) == bindings

    @priority.medium
    def test_1_compare_bindings_list_with_cf(self, sample_java_app):
        platform_bindings_list = ServiceBinding.api_get_list(sample_java_app.guid)
        cf_bindings_list = cf.cf_api_get_apps_bindings(sample_java_app.guid)['resources']
        assert len(cf_bindings_list) == len(platform_bindings_list) and len(cf_bindings_list)

    @priority.medium
    def test_2_delete_binding(self, sample_java_app):
        self.__class__.binding.api_delete()
        bindings = sample_java_app.cf_api_get_summary()['service_names']
        assert bindings == []

    @priority.medium
    def test_3_compare_bindings_list_with_cf(self, sample_java_app):
        platform_bindings_list = ServiceBinding.api_get_list(sample_java_app.guid)
        cf_bindings_list = cf.cf_api_get_apps_bindings(sample_java_app.guid)['resources']
        assert cf_bindings_list == platform_bindings_list

@priority.low
class TestBindingErrors:
    NOT_EXISTING_GUID = "00000000-0000-0000-0000-000000000000"
    INCORRECT_GUID = "incorrect_guid"

    @pytest.fixture(scope="class")
    def test_instance(self, class_context, request, test_org, test_space):
        step("Create test instance")
        instance = ServiceInstance.api_create_with_plan_name(class_context, test_org.guid, test_space.guid,
                                                             ServiceLabels.MONGO_DB, service_plan_name=ServicePlan.FREE)

        return instance

    def test_cannot_bind_not_existing_service_instance(self, sample_python_app):
        step("Try to create service binding to a non-existing service instance")
        expected_error_message = ServiceCatalogHttpStatus.MSG_SERVICE_INST_NOT_FOUND.format(self.NOT_EXISTING_GUID)
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND, expected_error_message,
                                                ServiceBinding.api_create, sample_python_app.guid, self.NOT_EXISTING_GUID)

    def test_cannot_bind_instance_with_incorrect_guid(self, sample_python_app):
        step("Try to create service binding with an incorrect service instance guid")
        assertions.assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_BAD_REQUEST,
                                                ServiceCatalogHttpStatus.MSG_BAD_REQUEST,
                                                ServiceBinding.api_create, sample_python_app.guid, self.INCORRECT_GUID)

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
