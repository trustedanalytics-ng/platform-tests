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
from modules.tap_object_model import CatalogService
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.catalog,)
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogServices:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
    SAMPLE_SERVICE_DESCRIPTION = "test-description"

    @pytest.fixture(scope="function")
    def catalog_service(self, context, catalog_template):
        log_fixture("Create sample catalog service")
        return CatalogService.create(context, template_id=catalog_template.id,
                                     description=self.SAMPLE_SERVICE_DESCRIPTION, state=TapEntityState.DEPLOYING)

    @priority.high
    def test_create_and_delete_catalog_service(self, context, catalog_template):
        """
        <b>Description:</b>
        Checks if new service can be created and deleted.

        <b>Input data:</b>
        1. sample catalog template

        <b>Expected results:</b>
        Test passes when new service can be created and deleted. According to this, service should be available on the
        list of services after being created and shouldn't be on this list after deletion.

        <b>Steps:</b>
        1. Create catalog service.
        2. Check that the service is on the list of catalog services.
        3. Delete the service.
        4. Check that service is no longer on the list of catalog services.
        """
        step("Create catalog service")
        catalog_service = CatalogService.create(context, template_id=catalog_template.id)

        step("Check that the service is on the list of catalog services")
        services = CatalogService.get_list()
        assert catalog_service in services

        step("Delete the service")
        catalog_service.delete()

        step("Check that the service is not on the list of catalog services")
        services = CatalogService.get_list()
        assert catalog_service not in services

        step("Check that getting the deleted service returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogService.get, service_id=catalog_service.id)

    @priority.high
    def test_update_service_description(self, context, catalog_template):
        """
        <b>Description:</b>
        Checks if service description can be updated.

        <b>Input data:</b>
        1. sample catalog template

        <b>Expected results:</b>
        Test passes when service description can be updated.

        <b>Steps:</b>
        1. Create catalog service with description test1.
        2. Update service description on test12.
        3. Check that the service was updated.
        """
        step("Create catalog service with description test1")
        catalog_service = CatalogService.create(context, template_id=catalog_template.id, description="test1")
        step("Update service description")
        catalog_service.update(field_name="description", value="test12")
        step("Check that the service was updated")
        service = CatalogService.get(service_id=catalog_service.id)
        assert service == catalog_service

    @priority.high
    def test_update_service_state(self, context, catalog_template):
        """
        <b>Description:</b>
        Checks if service state can be updated.

        <b>Input data:</b>
        1. sample catalog template

        <b>Expected results:</b>
        Test passes when service state can be updated.

        <b>Steps:</b>
        1. Create catalog service in state DEPLOYING
        2. Update service state on READY.
        3. Check that the service was updated.
        """
        step("Create catalog service in state DEPLOYING")
        catalog_service = CatalogService.create(context, template_id=catalog_template.id,
                                                state=TapEntityState.DEPLOYING)
        step("Update service state")
        catalog_service.update(field_name="state", value=TapEntityState.READY)
        step("Check that the service was updated")
        service = CatalogService.get(service_id=catalog_service.id)
        assert service == catalog_service

    @priority.low
    def test_cannot_add_service_with_existing_service_name(self, context, catalog_template, catalog_service):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating service with name which already exists.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service

        <b>Expected results:</b>
        Test passes when service with name which already exists is not created and status code 409 with error message:
        'service with name: {sample_service_name} already exists!' is returned.

        <b>Steps:</b>
        1. Create service with name which already exists on platform.
        """
        step("Add existing service")
        expected_message = CatalogHttpStatus.MSG_SERVICE_EXISTS.format(catalog_service.name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, expected_message,
                                     CatalogService.create, context, template_id=catalog_template.id,
                                     name=catalog_service.name)

    @priority.low
    def test_cannot_add_service_with_incorrect_name(self, context, catalog_template):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating service with incorrect name.

        <b>Input data:</b>
        1. sample catalog template
        2. invalid name: 'testServiceId'

        <b>Expected results:</b>
        Test passes when service is not created and status code 400 with error message:
        'Field: Name has incorrect value: testServiceId' is returned.

        <b>Steps:</b>
        1. Create service with incorrect name.
        """
        step("Create catalog service with incorrect name")
        incorrect_name = "testServiceId"
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(incorrect_name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogService.create, context, template_id=catalog_template.id,
                                     name=incorrect_name)

    @priority.medium
    def test_cannot_get_non_existent_service(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of getting service using not existing service id.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when service is not found on the list of services and status code: 404 with message: '100: Key not
        found' is returned.

        <b>Steps:</b>
        1. Get service using not existing service id.
        """
        step("Check that it's not possible to get service with non-existent service_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogService.get, service_id=self.INVALID_ID)

    @priority.low
    def test_cannot_update_service_with_wrong_prev_description_value(self, catalog_service):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating service field description giving value description and
        wrong prev_value of description.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service with description: 'test-description'
        3. new value of description: 'new-test-description'
        4. wrong prev_value of description: 'prev-test-description'

        <b>Expected results:</b>
        Test passes when service is not updated and status code 400 with error message:
        '101: Compare failed ([\\\"prev-test-description\\\" != \\\"test-description\\\"] is returned.

        <b>Steps:</b>
        1. Update service field description giving values: description and wrong prev_value of description.
        """
        step("Check that is't not possible to update service with incorrect prev_value of description")
        wrong_prev_description = "prev-test-description"
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(wrong_prev_description,
                                                                       self.SAMPLE_SERVICE_DESCRIPTION)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service.update, field_name="description", value="new-test-description",
                                     prev_value=wrong_prev_description)

    @priority.low
    def test_cannot_update_service_with_wrong_prev_state_value(self, catalog_service):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating service field state giving value state and
        wrong prev_value of state.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service in state DEPLOYING
        3. new value of state: READY
        4. wrong prev_value of state: OFFLINE

        <b>Expected results:</b>
        Test passes when service is not updated and status code 400 with error message:
        '101: Compare failed ([\\\"OFFLINE\\\" != \\\"DEPLOYING\\\"] is returned.

        <b>Steps:</b>
        1. Update service field state giving values: state and wrong prev_value of state.
        """
        step("Check that is't not possible to update service with incorrect prev_value of state")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapEntityState.OFFLINE,
                                                                       TapEntityState.DEPLOYING)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service.update, field_name="state", value=TapEntityState.READY,
                                     prev_value=TapEntityState.OFFLINE)

    @priority.low
    def test_cannot_update_service_state_to_non_existent_state(self, catalog_service):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating service state to not existing state.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service
        3. state: 'WRONG_STATE'

        <b>Expected results:</b>
        Test passes when service is not updated and status code 400 with error message: 'event WRONG_STATE does not
        exist' is returned.

        <b>Steps:</b>
        1. Update service state to not existing state.
        """
        step("Update the service state to non-existent state")
        wrong_state = "WRONG_STATE"
        expected_message = CatalogHttpStatus.MSG_EVENT_DOES_NOT_EXIST.format(wrong_state)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service.update, field_name="state", value=wrong_state)

    @priority.low
    def test_cannot_update_service_without_field(self, catalog_service):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating service omitting argument: field.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service

        <b>Expected results:</b>
        Test passes when service is not updated and status code 400 with error message: 'field field is empty!' is
        returned.

        <b>Steps:</b>
        1. Update service omitting argument: field.
        """
        step("Check that it's not possible to update service without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_service,
                                     service_id=catalog_service.id, field_name=None, value=TapEntityState.READY)

    @priority.low
    def test_cannot_update_service_without_value(self, catalog_service):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating service omitting argument: value.

        <b>Input data:</b>
        1. sample catalog template
        2. sample catalog service

        <b>Expected results:</b>
        Test passes when service is not updated and status code 400 with error message: 'field value is
        empty!' is returned.

        <b>Steps:</b>
        1. Update service omitting argument: value.
        """
        step("Check that it's not possible to update service without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_service,
                                     service_id=catalog_service.id, field_name="state", value=None)

    @priority.low
    def test_cannot_update_non_existent_service(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating not existing service.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'
        2. service state: 'READY'

        <b>Expected results:</b>
        Test passes when service is not updated and status code 404 with error message: '100: Key not found' is
        returned.

        <b>Steps:</b>
        1. Update service giving invalid service id.
        """
        step("Check that it's not possible to update non-existent service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_service, service_id=self.INVALID_ID, field_name="state",
                                     value=TapEntityState.READY)

    @priority.low
    def test_cannot_delete_non_existent_service(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of deleting not existing service.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when there is no possibility of deleting service and status code 404 with error message: '100: Key
        not found' is returned.

        <b>Steps:</b>
        1. Delete service giving invalid image id.
        """
        step("Check that it's not possible to delete non-existent service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_service, service_id=self.INVALID_ID)
