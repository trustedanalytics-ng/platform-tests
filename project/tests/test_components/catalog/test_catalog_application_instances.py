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

from modules.constants import CatalogHttpStatus, Guid, TapEntityState, TapComponent as TAP
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogApplicationInstance
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogApplicationInstances:

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
        """
        <b>Description:</b>
        Checks if new instance of application can be created and deleted.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application

        <b>Expected results:</b>
        Test passes when new instance of application can be created and deleted. According to this, instance should be
        available on the list of application instances after being created and shouldn't be on this list after deletion.

        <b>Steps:</b>
        1. Create application instance.
        2. Check that the instance is on the list of catalog application instances.
        3. Stop the application instance if their state is RUNNING.
        4. Delete the application instance.
        5. Check that application instance is no longer on the list of catalog application instances.
        """
        step("Create application instance")
        app_instance = CatalogApplicationInstance.create(context, application_id=catalog_application.id)

        step("Check that the instance is on the list of catalog applications")
        instances = CatalogApplicationInstance.get_list_for_application(application_id=catalog_application.id)
        assert app_instance in instances

        step("Stop application instance if their state is RUNNING")
        if app_instance.state == TapEntityState.RUNNING:
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

    @priority.medium
    def test_cannot_update_application_instance_class_id(self, catalog_application_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating application instance field classId.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. sample catalog application instance
        5. new classId value

        <b>Expected results:</b>
        Test passes when field classId of application instance is not updated and status code 400 with error message:
        'ClassID fields can not be changed!' is returned.

        <b>Steps:</b>
        1. Update application instance field classId
        """
        step("Check that it's not possible to update instance class id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_CLASS_ID_CANNOT_BE_CHANGED,
                                     catalog_application_instance.update, field_name="classId",
                                     value=self.SAMPLE_CLASS_ID)
        step("Check that the instance was not updated")
        instance = CatalogApplicationInstance.get(application_id=catalog_application_instance.class_id,
                                                  instance_id=catalog_application_instance.id)
        assert catalog_application_instance == instance

    @priority.medium
    def test_cannot_create_application_instance_with_existing_name(self, context, catalog_application_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating application instance with name which already exists.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. sample catalog application instance

        <b>Expected results:</b>
        Test passes when application instance with name which already exists is not created and status code 409 with
        error message: 'instance with name: {instance_name} already exists!' is returned.

        <b>Steps:</b>
        1. Create application instance with name which already exists on platform.
        """
        step("Check that it's not possible to create instance with existing name")
        expected_message = CatalogHttpStatus.MSG_INSTANCE_EXISTS.format(catalog_application_instance.name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, expected_message,
                                     CatalogApplicationInstance.create, context,
                                     application_id=catalog_application_instance.class_id,
                                     name=catalog_application_instance.name)

    @priority.low
    def test_cannot_create_application_instance_without_name(self, context, catalog_application):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating application instance with empty name: "".

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application

        <b>Expected results:</b>
        Test passes when application instance with empty name "" is not created and status code 400 with error message:
        'Field: Name has incorrect value: ""' is returned.

        <b>Steps:</b>
        1. Create application instance with empty name: "".
        """
        step("Create application instance without name")
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.EMPTY_NAME)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogApplicationInstance.create, context, application_id=catalog_application.id,
                                     name=self.EMPTY_NAME)

    @priority.low
    def test_cannot_update_application_instance_name(self, catalog_application_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating application instance name.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. sample catalog application instance

        <b>Expected results:</b>
        Test passes when field name of application instance is not updated and status code 400 with message: 'ID and
        Name fields can not be changed!' is returned.

        <b>Steps:</b>
        1. Update application instance name.
        """
        step("Check that it's not possible to update name instance by application")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS,
                                     catalog_application_instance.update, field_name="name", value="Simple3")
        step("Check that the instance was not updated")
        instance = CatalogApplicationInstance.get(application_id=catalog_application_instance.class_id,
                                                  instance_id=catalog_application_instance.id)
        assert catalog_application_instance == instance

    @priority.low
    def test_cannot_create_instance_of_not_existing_application(self, context):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating instance of not-existing application.

        <b>Input data:</b>
        1. not-existing application id.

        <b>Expected results:</b>
        Test passes when application instance is not created and status code 404 with error message: 'application with
        id: {not_existing_id} does not exists!' is returned.

        <b>Steps:</b>
        1. Create instance of not-existing application.
        """
        step("Check that it's not possible to create instance of not-existing application")
        expected_message = CatalogHttpStatus.MSG_APPLICATION_DOES_NOT_EXIST.format(Guid.NON_EXISTING_GUID)
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, expected_message,
                                     CatalogApplicationInstance.create, context, application_id=Guid.NON_EXISTING_GUID)

    @priority.low
    def test_cannot_create_application_instance_with_invalid_name(self, context, catalog_application):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating application instance with invalid name.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. invalid name: 'instance!#'

        <b>Expected results:</b>
        Test passes when application instance is not created and status code 400 with error message: 'Field: Name has
        incorrect value: instance!#' is returned.

        <b>Steps:</b>
        1. Create application instance with incorrect name.
        """
        step("Try to create instance with name '{}'".format(self.INCORRECT_INSTANCE_NAME))
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.INCORRECT_INSTANCE_NAME)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogApplicationInstance.create, context, application_id=catalog_application.id,
                                     name=self.INCORRECT_INSTANCE_NAME)

    @priority.low
    def test_cannot_get_application_instances_with_invalid_application_id(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of getting application instance using invalid application id.

        <b>Input data:</b>
        1. invalid id: '0123456789-9876543210'

        <b>Expected results:</b>
        Test passes when application instance is not found on the list of application instances and status code: 404 with message: '100: Key not found' is returned.

        <b>Steps:</b>
        1. Get application instance with incorrect application id.
        """
        step("List instances with invalid application id")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.get_application_instances, application_id=Guid.INVALID_GUID)

    @priority.low
    def test_cannot_create_instance_with_empty_body(self, catalog_application):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating application instance with empty body: {}.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application

        <b>Expected results:</b>
        Test passes when application instance is not created and status code 400 with error message: 'Field: Name has
        incorrect value: ' is returned.

        <b>Steps:</b>
        1. Create application instance with empty body: {}.
        """
        step("Check create instance with empty body")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.EMPTY_NAME),
                                     catalog_api.create_application_instance, application_id=catalog_application.id,
                                     name=None, instance_type=None, state=None)

    @priority.low
    def test_cannot_get_not_existing_application_instance(self, catalog_application):
        """
        <b>Description:</b>
        Checks if there is no possibility of getting application instance using invalid instance id.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. invalid id: 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF'

        <b>Expected results:</b>
        Test passes when application instance is not found on the list of application instances and status code: 404
        with message: '100: Key not found' is returned.

        <b>Steps:</b>
        1. Get application instance with incorrect instance id.
        """
        step("Check that getting not-existing application instance causes an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogApplicationInstance.get, application_id=catalog_application.id,
                                     instance_id=Guid.NON_EXISTING_GUID)

    @priority.low
    def test_cannot_update_application_instance_with_wrong_prev_class_id_value(self, catalog_application_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating application instance field classId giving value classId and
        wrong prev_value of classId.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. sample catalog application instance
        5. new classId value
        6. wrong prev_value of classId

        <b>Expected results:</b>
        Test passes when field classId of application instance is not updated and status code 400 with error message:
        'ClassID fields can not be changed!' is returned.

        <b>Steps:</b>
        1. Update application instance field classId giving values: classId and wrong prev_value of classId.
        """
        step("Check that is't not possible to update application instance with incorrect prev_value of class id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_CLASS_ID_CANNOT_BE_CHANGED,
                                     catalog_application_instance.update, field_name="classId", value=self.NEW_CLASS_ID,
                                     prev_value=self.WRONG_PREV_CLASS_ID)
        step("Check that the instance was not updated")
        instance = CatalogApplicationInstance.get(application_id=catalog_application_instance.class_id,
                                                  instance_id=catalog_application_instance.id)
        assert catalog_application_instance == instance

    @priority.low
    def test_cannot_update_application_instance_without_field(self, catalog_application_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating application instance omitting argument: field.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. sample catalog application instance
        5. new classId value

        <b>Expected results:</b>
        Test passes when application instance is not updated and status code 400 with error message: 'field field is
        empty!' is returned.

        <b>Steps:</b>
        1. Update application instance omitting argument: field.
        """
        step("Check that it's not possible to update application instance without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_application_instance.update, field_name=None, value=self.NEW_CLASS_ID)
        step("Check that the instance was not updated")
        instance = CatalogApplicationInstance.get(application_id=catalog_application_instance.class_id,
                                                  instance_id=catalog_application_instance.id)
        assert catalog_application_instance == instance

    @priority.low
    def test_cannot_update_application_without_value(self, catalog_application_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating application instance omitting argument: value.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. sample catalog application instance
        5. field: 'classId'

        <b>Expected results:</b>
        Test passes when application instance is not updated and status code 400 with error message: 'field value is
        empty!' is returned.

        <b>Steps:</b>
        1. Update application instance omitting argument: value.
        """
        step("Check that it's not possible to update application instance without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_application_instance.update, field_name="classId", value=None)

    @priority.low
    def test_cannot_update_not_existing_application_instance(self, catalog_application_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating application instance giving invalid instance id.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. sample catalog application instance
        5. new classId value
        6. invalid id: 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF'

        <b>Expected results:</b>
        Test passes when application instance is not updated and status code 404 with error message: '100: Key not
        found' is returned.

        <b>Steps:</b>
        1. Update application instance giving invalid instance id.
        """
        step("Check that it's not possible to update not-existing application instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_application_instance,
                                     application_id=catalog_application_instance.class_id, instance_id=Guid.NON_EXISTING_GUID,
                                     field_name="classId", value=self.NEW_CLASS_ID)

    @priority.low
    def test_cannot_delete_not_existing_application_instance(self, catalog_application):
        """
        <b>Description:</b>
        Checks if there is no possibility of deleting not-existing application instance.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog image
        3. sample catalog application
        4. invalid id: 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF'

        <b>Expected results:</b>
        Test passes when there is no possibility of deleting application instance and status code 404 with error
        message: '100: Key not found' is returned.

        <b>Steps:</b>
        1. Delete application instance giving invalid instance id.
        """
        step("Check that it's not possible to delete not-existing application instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_application_instance, application_id=catalog_application.id,
                                     instance_id=Guid.NON_EXISTING_GUID)
