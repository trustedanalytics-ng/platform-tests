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

from modules.constants import CatalogHttpStatus, Guid, TapComponent as TAP
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogInstance, CatalogServiceInstance
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogInstances:

    SAMPLE_CLASS_ID = "test-class"
    NEW_CLASS_ID = "new-class-id"
    WRONG_PREV_CLASS_ID = "prev-test-class-id"
    INCORRECT_INSTANCE_NAME = "instance!#"

    @pytest.fixture(scope="class")
    def catalog_service_instance(self, class_context, catalog_service):
        log_fixture("Create service instance in catalog")
        return CatalogServiceInstance.create(class_context, service_id=catalog_service.id,
                                             plan_id=catalog_service.plans[0].id)

    @pytest.fixture(scope="class")
    def catalog_instance(self, catalog_service_instance):
        log_fixture("Get service instance from the list of all instances")
        instances = CatalogInstance.get_all()
        instance = next(i for i in instances if i.id == catalog_service_instance.id)
        assert instance is not None, "Service instance was not found on the list of all instances"
        return instance

    @priority.high
    def test_create_and_delete_instance(self, context, catalog_service):
        """
        <b>Description:</b>
        Checks if instance can be created and deleted.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service

        <b>Expected results:</b>
        Test passes when new instance can be created and deleted. According to this, instance should be available on
        the list of instances after being created and shouldn't be on this list after deletion.

        <b>Steps:</b>
        1. Create service instance in catalog.
        2. Check that the service instance is on the list of all instances.
        3. Delete instance.
        4. Check that instance was deleted.
        5. Check that getting the deleted instance returns an error.
        """
        step("Create service instance in catalog")
        catalog_instance = CatalogServiceInstance.create(context, service_id=catalog_service.id,
                                                         plan_id=catalog_service.plans[0].id)
        step("Check that the service instance is on the list of all instances")
        instances = CatalogInstance.get_all()
        assert catalog_instance in instances
        step("Delete instance")
        catalog_instance.delete()
        step("Check that the instance was deleted")
        instances = CatalogInstance.get_all()
        assert catalog_instance not in instances

        # TODO this error message should be different
        step("Check that getting the deleted instance returns an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogInstance.get, instance_id=catalog_instance.id)

    @priority.medium
    def test_cannot_update_instance_class_id(self, catalog_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating instance field classId.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        3. sample catalog service instance
        4. new classId value

        <b>Expected results:</b>
        Test passes when field classId of instance is not updated and status code 400 with error message:
        'ClassID fields can not be changed!' is returned.

        <b>Steps:</b>
        1. Update instance field classId
        """
        step("Check that it's not possible to update instance class id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_CLASS_ID_CANNOT_BE_CHANGED,
                                     catalog_instance.update, field_name="classId", value=self.SAMPLE_CLASS_ID)

    @priority.low
    def test_cannot_get_not_existing_instance(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of getting instance using not-existing instance id.

        <b>Input data:</b>
        1. id: 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF'

        <b>Expected results:</b>
        Test passes when instance is not found on the list of instances and status code: 404 with message: '100: Key
        not found' is returned.

        <b>Steps:</b>
        1. Get instance using not-existing instance id.
        """
        step("Check that getting instance with incorrect id causes an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogInstance.get, instance_id=Guid.NON_EXISTING_GUID)

    @priority.low
    def test_cannot_update_instance_name(self, catalog_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating instance name.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        3. sample catalog service instance

        <b>Expected results:</b>
        Test passes when instance is not updated and status code: 400 with message: 'ID and Name fields can not be
        changed!' is returned.

        <b>Steps:</b>
        1. Update sample instance name.
        2. Check that the instance was not updated.
        """
        step("Check that it's not possible to update instance name")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS,
                                     catalog_instance.update, field_name="name", value="Simple3")
        step("Check that the instance was not updated")
        instance = CatalogInstance.get(instance_id=catalog_instance.id)
        assert catalog_instance == instance

    @priority.low
    @pytest.mark.bugs("DPNG-13600: User can update catalog instance using wrong prevValue classId")
    def test_cannot_update_instance_with_wrong_prev_class_id_value(self, catalog_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating instance field classId giving value classId and wrong prev_value
        of classId.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        3. sample catalog service instance
        4. new classId value
        5. wrong prev_value of classId

        <b>Expected results:</b>
        Test passes when field classId of instance is not updated and status code 400 with error message:
        'ClassID fields can not be changed!' is returned.

        <b>Steps:</b>
        1. Update instance field classId giving values: classId and wrong prev_value of classId.
        """
        step("Check that is't not possible to update instance with incorrect prev_value of class id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_CLASS_ID_CANNOT_BE_CHANGED,
                                     catalog_instance.update, field_name="classId", value=self.NEW_CLASS_ID,
                                     prev_value=self.WRONG_PREV_CLASS_ID)
        step("Check that the instance was not updated")
        instance = CatalogInstance.get(instance_id=catalog_instance.id)
        assert catalog_instance == instance

    @priority.low
    def test_cannot_update_instance_without_field(self, catalog_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating instance omitting argument: field.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        3. sample catalog service instance
        4. new classId

        <b>Expected results:</b>
        Test passes when instance is not updated and status code 400 with error message: 'field field is empty!' is
        returned.

        <b>Steps:</b>
        1. Update instance omitting argument: field.
        """
        step("Check that it's not possible to update instance without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_instance.update, field_name=None, value=self.NEW_CLASS_ID)
        step("Check that the instance was not updated")
        instance = CatalogInstance.get(instance_id=catalog_instance.id)
        assert catalog_instance == instance

    @priority.low
    def test_cannot_update_instance_without_value(self, catalog_instance):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating instance omitting argument: value.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        3. sample catalog service instance

        <b>Expected results:</b>
        Test passes when instance is not updated and status code 400 with error message: 'field value is empty!' is
        returned.

        <b>Steps:</b>
        1. Update instance omitting argument: value.
        """
        step("Check that it's not possible to update instance without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_instance.update, field_name="classId", value=None)
        step("Check that the instance was not updated")
        instance = CatalogInstance.get(instance_id=catalog_instance.id)
        assert catalog_instance == instance

    @priority.low
    def test_cannot_update_not_existing_instance(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating instance giving not-existing instance id.

        <b>Input data:</b>
        1. invalid id: 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF'

        <b>Expected results:</b>
        Test passes when instance is not updated and status code 404 with error message: '100: Key not found' is
        returned.

        <b>Steps:</b>
        1. Update instance giving not-existing instance id.
        """
        step("Check that it's not possible to update not-existing instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_instance, instance_id=Guid.NON_EXISTING_GUID, field_name="classId",
                                     value=self.NEW_CLASS_ID)

    @priority.low
    def test_cannot_delete_not_existing_instance(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of deleting instance giving not-existing instance id.

        <b>Input data:</b>
        1. invalid id: 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF'

        <b>Expected results:</b>
        Test passes when instance is not deleted and status code 404 with error message: '100: Key not found' is
        returned.

        <b>Steps:</b>
        1. Delete instance giving not-existing instance id.
        """
        step("Check that it's not possible to delete not-existing instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_instance, instance_id=Guid.NON_EXISTING_GUID)
