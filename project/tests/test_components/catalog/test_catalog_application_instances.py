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

from modules.constants import CatalogHttpStatus, TapEntityState, TapComponent as TAP
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogApplicationInstance
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogApplicationInstances:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
    SAMPLE_CLASS_ID = "test-class"
    NEW_CLASS_ID = "new-class-id"
    WRONG_PREV_CLASS_ID = "prev-test-class-id"
    INCORRECT_INSTANCE_NAME = "instance!#"
    EMPTY_NAME = ""

    @pytest.fixture(scope="class")
    def catalog_application_instance(self, class_context, catalog_application):
        log_fixture("Create sample catalog application instance")
        return CatalogApplicationInstance.create(class_context, application_id=catalog_application.id)

    @priority.high
    def test_create_and_delete_application_instance(self, context, catalog_application):
        step("Create application instance")
        app_instance = CatalogApplicationInstance.create(context, application_id=catalog_application.id)

        step("Check that the instance is on the list of catalog applications")
        instances = CatalogApplicationInstance.get_list_for_application(application_id=catalog_application.id)
        assert app_instance in instances

        step("Stop application")
        app_instance.stop()
        app_instance.ensure_in_state(expected_state=TapEntityState.STOPPED)
        step("Delete the application instance")
        app_instance.delete()

        step("Check the application instance is no longer on the list")
        instances = CatalogApplicationInstance.get_all()
        assert app_instance not in instances

        # TODO this error message should be different
        step("Check that getting the deleted application instance returns an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogApplicationInstance.get, application_id=catalog_application.id,
                                     instance_id=app_instance.id)

    @priority.high
    def test_update_application_instance_class_id(self, context, catalog_application):
        step("Create application instance in catalog")
        test_instance = CatalogApplicationInstance.create(context, application_id=catalog_application.id)
        step("Get class id for application instance before update")
        class_id_before_update = test_instance.class_id
        step("Update application instance class id")
        test_instance.update(field_name="classId", value=self.SAMPLE_CLASS_ID)
        step("Check that the application instance was updated")
        instance = CatalogApplicationInstance.get(application_id=catalog_application.id, instance_id=test_instance.id)
        assert test_instance == instance

        step("Update application instance class id value to the original value")
        test_instance.class_id = class_id_before_update
        test_instance.update(field_name="classId", value=class_id_before_update)
        step("Check that the application instance was updated to the original value")
        instance = CatalogApplicationInstance.get(application_id=catalog_application.id, instance_id=test_instance.id)
        assert test_instance == instance

    @priority.medium
    def test_cannot_create_application_instance_with_existing_name(self, context, catalog_application_instance):
        step("Check that it's not possible to create instance with existing name")
        expected_message = CatalogHttpStatus.MSG_INSTANCE_EXISTS.format(catalog_application_instance.name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, expected_message,
                                     CatalogApplicationInstance.create, context,
                                     application_id=catalog_application_instance.class_id,
                                     name=catalog_application_instance.name)

    @priority.low
    def test_cannot_create_application_instance_without_name(self, context, catalog_application):
        step("Create application instance without name")
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.EMPTY_NAME)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogApplicationInstance.create, context, application_id=catalog_application.id,
                                     name=self.EMPTY_NAME)

    @priority.low
    def test_cannot_update_application_instance_name(self, catalog_application_instance):
        step("Check that it's not possible to update name instance by application")
        assert_raises_http_exception(CatalogHttpStatus.CODE_INTERNAL_SERVER_ERROR,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS,
                                     catalog_application_instance.update, field_name="name", value="Simple3")
        step("Check that the instance was not updated")
        instance = CatalogApplicationInstance.get(application_id=catalog_application_instance.class_id,
                                                  instance_id=catalog_application_instance.id)
        assert catalog_application_instance == instance

    @priority.low
    def test_cannot_create_instance_of_not_existing_application(self, context):
        step("Check that it's not possible to create instance of not-existing application")
        expected_message = CatalogHttpStatus.MSG_APPLICATION_DOES_NOT_EXIST.format(self.INVALID_ID)
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, expected_message,
                                     CatalogApplicationInstance.create, context, application_id=self.INVALID_ID)

    @priority.low
    def test_cannot_create_application_instance_with_invalid_name(self, context, catalog_application):
        step("Try to create instance with name '{}'".format(self.INCORRECT_INSTANCE_NAME))
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.INCORRECT_INSTANCE_NAME)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogApplicationInstance.create, context, application_id=catalog_application.id,
                                     name=self.INCORRECT_INSTANCE_NAME)

    @priority.low
    def test_cannot_get_application_instances_with_invalid_application_id(self):
        invalid_id = "90982774-09198298"
        step("List instances with invalid application id")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.get_application_instances, application_id=invalid_id)

    @priority.low
    def test_cannot_create_instance_with_empty_body(self, catalog_application):
        step("Check create instance with empty body")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.EMPTY_NAME),
                                     catalog_api.create_application_instance, application_id=catalog_application.id,
                                     name=None, instance_type=None, state=None)

    @priority.low
    def test_cannot_get_not_existing_application_instance(self, catalog_application):
        step("Check that getting not-existing application instance causes an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogApplicationInstance.get, application_id=catalog_application.id,
                                     instance_id=self.INVALID_ID)

    @priority.low
    @pytest.mark.bugs("DPNG-13298: Wrong status code after send PATCH with wrong prev_value (catalog: services, "
                      "catalog: applications)")
    def test_cannot_update_application_instance_with_wrong_prev_class_id_value(self, catalog_application_instance):
        step("Check that is't not possible to update application instance with incorrect prev_value of class id")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(self.WRONG_PREV_CLASS_ID,
                                                                       catalog_application_instance.class_id)
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message,
                                     catalog_application_instance.update, field_name="classId", value=self.NEW_CLASS_ID,
                                     prev_value=self.WRONG_PREV_CLASS_ID)

    @priority.low
    @pytest.mark.bugs("DPNG-13300: Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: services, catalog: applications)")
    def test_cannot_update_application_instance_without_field(self, catalog_application_instance):
        step("Check that it's not possible to update application instance without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message,
                                     catalog_application_instance.update, field_name=None, value=self.NEW_CLASS_ID)

    @priority.low
    @pytest.mark.bugs("DPNG-13300: Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: services, catalog: applications)")
    def test_cannot_update_application_without_value(self, catalog_application_instance):
        step("Check that it's not possible to update application instance without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message,
                                     catalog_application_instance.update, field_name="classId", value=None)

    @priority.low
    def test_cannot_update_not_existing_application_instance(self, catalog_application_instance):
        step("Check that it's not possible to update not-existing application instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_application_instance,
                                     application_id=catalog_application_instance.class_id, instance_id=self.INVALID_ID,
                                     field_name="classId", value=self.NEW_CLASS_ID)

    @priority.low
    def test_cannot_delete_not_existing_application_instance(self, catalog_application):
        step("Check that it's not possible to delete not-existing application instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_application_instance, application_id=catalog_application.id,
                                     instance_id=self.INVALID_ID)
