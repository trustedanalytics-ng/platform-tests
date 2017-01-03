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
        step("Create catalog service with description test1")
        catalog_service = CatalogService.create(context, template_id=catalog_template.id, description="test1")
        step("Update service description")
        catalog_service.update(field_name="description", value="test12")
        step("Check that the service was updated")
        service = CatalogService.get(service_id=catalog_service.id)
        assert service == catalog_service

    @priority.high
    def test_update_service_state(self, context, catalog_template):
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
        step("Add existing service")
        expected_message = CatalogHttpStatus.MSG_SERVICE_EXISTS.format(catalog_service.name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, expected_message,
                                     CatalogService.create, context, template_id=catalog_template.id,
                                     name=catalog_service.name)

    @priority.low
    def test_cannot_add_service_with_incorrect_name(self, context, catalog_template):
        step("Create catalog service with incorrect name")
        incorrect_name = "testServiceId"
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(incorrect_name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogService.create, context, template_id=catalog_template.id,
                                     name=incorrect_name)

    @priority.medium
    def test_cannot_get_non_existent_service(self):
        step("Check that it's not possible to get service with non-existent service_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogService.get, service_id=self.INVALID_ID)

    @priority.low
    def test_cannot_update_service_with_wrong_prev_description_value(self, catalog_service):
        step("Check that is't not possible to update service with incorrect prev_value of description")
        wrong_prev_description = "prev-test-description"
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(wrong_prev_description,
                                                                       self.SAMPLE_SERVICE_DESCRIPTION)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service.update, field_name="description", value="new-test-description",
                                     prev_value=wrong_prev_description)

    @priority.low
    def test_cannot_update_service_with_wrong_prev_state_value(self, catalog_service):
        step("Check that is't not possible to update service with incorrect prev_value of state")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapEntityState.OFFLINE,
                                                                       TapEntityState.DEPLOYING)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service.update, field_name="state", value=TapEntityState.READY,
                                     prev_value=TapEntityState.OFFLINE)

    @priority.low
    def test_cannot_update_service_state_to_non_existent_state(self, catalog_service):
        step("Update the service state to non-existent state")
        wrong_state = "WRONG_STATE"
        expected_message = CatalogHttpStatus.MSG_EVENT_DOES_NOT_EXIST.format(wrong_state)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_service.update, field_name="state", value=wrong_state)

    @priority.low
    def test_cannot_update_service_without_field(self, catalog_service):
        step("Check that it's not possible to update service without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_service,
                                     service_id=catalog_service.id, field_name=None, value=TapEntityState.READY)

    @priority.low
    def test_cannot_update_service_without_value(self, catalog_service):
        step("Check that it's not possible to update service without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_service,
                                     service_id=catalog_service.id, field_name="state", value=None)

    @priority.low
    def test_cannot_update_non_existent_service(self):
        step("Check that it's not possible to update non-existent service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_service, service_id=self.INVALID_ID, field_name="state",
                                     value=TapEntityState.READY)

    @priority.low
    def test_cannot_delete_non_existent_service(self):
        step("Check that it's not possible to delete non-existent service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_service, service_id=self.INVALID_ID)
