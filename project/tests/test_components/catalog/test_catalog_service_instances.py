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

from modules.constants import CatalogHttpStatus, TapComponent as TAP
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogInstance, CatalogServiceInstance
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogServiceInstances:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
    SAMPLE_CLASS_ID = "test-class"
    NEW_CLASS_ID = "new-class-id"
    WRONG_PREV_CLASS_ID = "prev-test-class-id"
    INCORRECT_INSTANCE_NAME = "instance!#"
    EMPTY_NAME = ""

    @pytest.fixture(scope="class")
    def catalog_service_instance(self, class_context, catalog_service):
        log_fixture("Create sample catalog service instance")
        return CatalogServiceInstance.create(class_context, service_id=catalog_service.id,
                                             plan_id=catalog_service.plans[0].id)

    @priority.high
    def test_create_and_delete_service_instance_in_catalog(self, context, catalog_service):
        step("Create service instance in catalog")
        catalog_service_instance = CatalogServiceInstance.create(context, service_id=catalog_service.id,
                                                                 plan_id=catalog_service.plans[0].id)

        step("Check that the service instance is on the list of all instances")
        instances = CatalogInstance.get_all()
        assert catalog_service_instance in instances

        step("Check that the service instance is on the list of all service instances")
        service_instances = CatalogServiceInstance.get_all()
        assert catalog_service_instance in service_instances

        step("Check that the service instance is on the list of service instances for the service")
        service_instances = CatalogServiceInstance.get_list_for_service(service_id=catalog_service.id)
        assert catalog_service_instance in service_instances

        step("Delete the service instance")
        catalog_service_instance.delete()

        step("Check that getting the deleted service instance returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogServiceInstance.get, service_id=catalog_service.id,
                                     instance_id=catalog_service_instance.id)

    @priority.high
    def test_cannot_update_service_instance_class_id(self, catalog_service_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating service instance field classId.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        4. sample catalog service instance
        5. new classId value

        <b>Expected results:</b>
        Test passes when field classId of service instance is not updated and status code 400 with error message:
        'ClassID fields can not be changed!' is returned.

        <b>Steps:</b>
        1. Update service instance field classId
        """
        step("Check that it's not possible to update instance class id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_CLASS_ID_CANNOT_BE_CHANGED,
                                     catalog_service_instance.update, field_name="classId", value=self.SAMPLE_CLASS_ID)

    @priority.medium
    def test_cannot_create_service_instance_without_plan_id(self, context, catalog_service):
        step("Check that it's not possible to create instance without plan_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, CatalogHttpStatus.MSG_KEY_PLAN_ID_NOT_FOUND,
                                     CatalogServiceInstance.create, context, service_id=catalog_service.id)

    @priority.medium
    def test_cannot_create_service_instance_with_existing_name(self, context, catalog_service,
                                                               catalog_service_instance):
        step("Check that it's not possible to create instance with existing name")
        expected_message = CatalogHttpStatus.MSG_INSTANCE_EXISTS.format(catalog_service_instance.name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, expected_message, CatalogServiceInstance.create,
                                     context, service_id=catalog_service.id, plan_id=catalog_service.plans[0].id,
                                     name=catalog_service_instance.name)

    @priority.low
    def test_cannot_create_service_instance_without_name(self, context, catalog_service):
        step("Create service instance without name")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.EMPTY_NAME),
                                     CatalogServiceInstance.create, context, service_id=catalog_service.id,
                                     plan_id=catalog_service.plans[0].id, name=self.EMPTY_NAME)

    @priority.low
    def test_cannot_update_service_instance_name(self, catalog_service_instance):
        step("Check that it's not possible to update name instance by service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS,
                                     catalog_service_instance.update, field_name="name", value="Simple3")
        step("Check that the instance was not updated")
        instance = CatalogServiceInstance.get(service_id=catalog_service_instance.class_id,
                                              instance_id=catalog_service_instance.id)
        assert catalog_service_instance == instance

    @priority.low
    def test_cannot_create_instance_of_not_existing_service(self, context):
        step("Check that it's not possible to create instance of not-existing service")
        expected_message = CatalogHttpStatus.MSG_SERVICE_DOES_NOT_EXIST.format(self.INVALID_ID)
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, expected_message,
                                     CatalogServiceInstance.create, context, service_id=self.INVALID_ID)

    @priority.low
    def test_cannot_get_instance_of_not_existing_service(self, catalog_service_instance):
        step("Check that getting instance with incorrect service id causes an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogServiceInstance.get, service_id=self.INVALID_ID,
                                     instance_id=catalog_service_instance.id)

    @priority.low
    def test_cannot_create_instance_with_invalid_name(self, context, catalog_service):
        step("Try to create instance with name '{}'".format(self.INCORRECT_INSTANCE_NAME))
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.INCORRECT_INSTANCE_NAME)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogServiceInstance.create, context, service_id=catalog_service.id,
                                     name=self.INCORRECT_INSTANCE_NAME, plan_id=catalog_service.plans[0].id)

    @priority.low
    def test_cannot_create_instance_with_empty_body(self, catalog_service):
        step("Check create instance with empty body")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, CatalogHttpStatus.MSG_KEY_PLAN_ID_NOT_FOUND,
                                     catalog_api.create_service_instance, service_id=catalog_service.id, name=None,
                                     instance_type=None, state=None)

    @priority.low
    def test_cannot_get_not_existing_service_instance(self, catalog_service):
        step("Check that getting not-existing service instance causes an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogServiceInstance.get, service_id=catalog_service.id,
                                     instance_id=self.INVALID_ID)

    @priority.low
    def test_cannot_update_service_instance_with_wrong_prev_class_id_value(self, catalog_service_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating service instance field classId giving value classID and
        wrong prev_value of classId.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        3. sample catalog service instance
        4. new classId value
        5. wrong prev_value of classId

        <b>Expected results:</b>
        Test passes when field classId of service instance is not updated and status code 400 with error message:
        'ClassID fields can not be changed!' is returned.

        <b>Steps:</b>
        1. Update service instance field classId giving values: classId and wrong prev_value of classId.
        """
        step("Check that is't not possible to update service instance with incorrect prev_value of class id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_CLASS_ID_CANNOT_BE_CHANGED,
                                     catalog_service_instance.update, field_name="classId", value=self.NEW_CLASS_ID,
                                     prev_value=self.WRONG_PREV_CLASS_ID)

    @priority.low
    def test_cannot_update_service_instance_without_field(self, catalog_service_instance):
        step("Check that it's not possible to update service instance without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service_instance.update, field_name=None, value=self.NEW_CLASS_ID)

    @priority.low
    def test_cannot_update_service_without_value(self, catalog_service_instance):
        step("Check that it's not possible to update service instance without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service_instance.update, field_name="classId", value=None)

    @priority.low
    def test_cannot_update_not_existing_service_instance(self, catalog_service_instance):
        step("Check that it's not possible to update not-existing service instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_service_instance, service_id=catalog_service_instance.class_id,
                                     instance_id=self.INVALID_ID, field_name="classId", value=self.NEW_CLASS_ID)

    @priority.low
    def test_cannot_delete_not_existing_service_instance(self, catalog_service):
        step("Check that it's not possible to delete not-existing service instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_service_instance, service_id=catalog_service.id,
                                     instance_id=self.INVALID_ID)
