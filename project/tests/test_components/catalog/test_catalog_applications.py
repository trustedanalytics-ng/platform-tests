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
from modules.tap_object_model import CatalogApplication
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogApplications:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
    SAMPLE_APPLICATION_DESCRIPTION = "test-description"
    SAMPLE_APPLICATION_REPLICATION = 1
    WRONG_PREV_REPLICA_VALUE = 3
    NON_INT_REPLICA_NUMBER = "WRONG_NUMBER"
    WRONG_PREV_DESCRIPTION = "prev-test-description"
    INCORRECT_APP_NAME = "testApplicationId"

    @pytest.fixture("class")
    def sample_app_image(self, class_context, catalog_template, catalog_image):
        log_fixture("Create sample catalog image")
        step("Create application in catalog")
        return CatalogApplication.create(class_context, template_id=catalog_template.id, image_id=catalog_image.id,
                                         description=self.SAMPLE_APPLICATION_DESCRIPTION)

    @priority.high
    def test_create_and_delete_application(self, context, catalog_template, catalog_image):
        step("Create application in catalog")
        catalog_application = CatalogApplication.create(context, template_id=catalog_template.id,
                                                        image_id=catalog_image.id)
        step("Check that application is on the list of catalog applications")
        applications = CatalogApplication.get_list()
        assert catalog_application in applications

        step("Delete the application")
        catalog_application.delete()

        step("Check that the application is not on the list")
        applications = CatalogApplication.get_list()
        assert catalog_application not in applications

        step("Check that getting the deleted application returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogApplication.get, application_id=catalog_application.id)

    @priority.high
    def test_update_application_replication(self, context, catalog_template, catalog_image):
        step("Create catalog application")
        catalog_application = CatalogApplication.create(context, template_id=catalog_template.id,
                                                        image_id=catalog_image.id)
        step("Update value of application replication")
        catalog_application.update(field_name="replication", value=2)
        step("Check that application was updated")
        application = CatalogApplication.get(application_id=catalog_application.id)
        assert catalog_application == application

    @priority.high
    def test_update_application_description(self, context, catalog_template, catalog_image):
        step("Create catalog application")
        catalog_application = CatalogApplication.create(context, template_id=catalog_template.id,
                                                        image_id=catalog_image.id, description="")
        step("Update value of application description")
        catalog_application.update(field_name="description", value=self.SAMPLE_APPLICATION_DESCRIPTION)
        step("Check that application was updated")
        application = CatalogApplication.get(application_id=catalog_application.id)
        assert catalog_application == application

    @priority.low
    def test_cannot_add_application_with_existing_application_name(self, context, sample_app_image):
        step("Add existing application")
        expected_message = CatalogHttpStatus.MSG_APPLICATION_EXISTS.format(sample_app_image.name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, expected_message,
                                     CatalogApplication.create, context, template_id=sample_app_image.template_id,
                                     image_id=sample_app_image.image_id, name=sample_app_image.name)

    @priority.low
    def test_cannot_add_application_with_incorrect_name(self, context, catalog_template, catalog_image):
        step("Create catalog application with incorrect name")
        expected_message = CatalogHttpStatus.MSG_APP_FORBIDDEN_CHARACTERS.format(self.INCORRECT_APP_NAME)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogApplication.create, context, template_id=catalog_template.id,
                                     image_id=catalog_image.id, name=self.INCORRECT_APP_NAME)

    @priority.low
    @pytest.mark.bugs("DPNG-13298: Wrong status code after send PATCH with wrong prev_value (catalog: services, "
                      "catalog: applications)")
    def test_cannot_update_application_with_wrong_prev_description_value(self, sample_app_image):
        step("Check that is't not possible to update application with incorrect prev_value of description")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(self.WRONG_PREV_DESCRIPTION,
                                                                       self.SAMPLE_APPLICATION_DESCRIPTION)
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message,
                                     sample_app_image.update, field_name="description", value="new-test-description",
                                     prev_value=self.WRONG_PREV_DESCRIPTION)

    @priority.low
    @pytest.mark.bugs("DPNG-13298: Wrong status code after send PATCH with wrong prev_value (catalog: services, "
                      "catalog: applications)")
    def test_cannot_update_application_with_wrong_prev_replication_value(self, sample_app_image):
        step("Check that is't not possible to update application with incorrect prev_value of replication")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(self.WRONG_PREV_REPLICA_VALUE,
                                                                       self.SAMPLE_APPLICATION_REPLICATION)
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message,
                                     sample_app_image.update, field_name="replication", value=2,
                                     prev_value=self.WRONG_PREV_REPLICA_VALUE)

    @priority.low
    @pytest.mark.bugs("DPNG-13416: Wrong status code and error messages for catalog requests.")
    def test_cannot_update_application_replication_to_non_int_number_of_replicas(self, sample_app_image):
        step("Update the template state to nonexistent state")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, CatalogHttpStatus.MSG_INCORRECT_TYPE,
                                     sample_app_image.update, field_name="replication",
                                     value=self.NON_INT_REPLICA_NUMBER)

    @priority.low
    @pytest.mark.bugs("DPNG-13300: Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: services, catalog: applications)")
    def test_cannot_update_application_without_field(self, sample_app_image):
        step("Check that it's not possible to update application without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message,
                                     catalog_api.update_application, application_id=sample_app_image.id, field_name=None,
                                     value=2)

    @priority.low
    @pytest.mark.bugs("DPNG-13300: Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: services, catalog: applications)")
    def test_cannot_update_application_without_value(self, sample_app_image):
        step("Check that it's not possible to update application without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message,
                                     catalog_api.update_application, application_id=sample_app_image.id,
                                     field_name="replication", value=None)

    @priority.low
    def test_cannot_update_non_existing_application(self):
        step("Check that it's not possible to update non-existing application")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_application, application_id=self.INVALID_ID,
                                     field_name="replication", value=2)

    @priority.low
    def test_cannot_delete_non_existing_application(self):
        step("Check that it's not possible to delete non-existing application")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_application, application_id=self.INVALID_ID)

    @priority.low
    def test_cannot_get_application_with_invalid_id(self):
        step("Check application with invalid application id")
        invalid_id = "90982774-09198298"
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.get_application, application_id=invalid_id)
