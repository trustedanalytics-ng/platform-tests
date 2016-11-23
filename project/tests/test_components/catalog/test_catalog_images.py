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

from modules.constants import CatalogHttpStatus, TapEntityState, TapApplicationType, TapComponent as TAP
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogImage
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogImages:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"

    @pytest.fixture(scope="class")
    def sample_catalog_image(self, class_context):
        log_fixture("Create sample catalog image")
        return CatalogImage.create(class_context, image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

    @priority.high
    def test_create_and_delete_catalog_image(self, context):
        step("Create catalog image")
        catalog_image = CatalogImage.create(context, image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

        step("Check that the image is on list of catalog images")
        images = CatalogImage.get_list()
        assert catalog_image in images

        step("Delete the image")
        catalog_image.delete()

        step("Check that the image was deleted")
        images = CatalogImage.get_list()
        assert catalog_image not in images

        step("Check that getting the deleted image returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogImage.get, image_id=catalog_image.id)

    @priority.medium
    def test_create_image_with_image_id(self, context):
        step("Create image with image_id")
        catalog_image = CatalogImage.create(context, image_id=generate_test_object_name(),
                                            image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)
        step("Check that the image is on the list of catalog images")
        images = CatalogImage.get_list()
        assert catalog_image in images

    @priority.low
    def test_create_image_with_empty_body(self, context):
        step("Create image with empty_body")
        catalog_image = CatalogImage.create(context)
        step("Check that the image is on the list of catalog images")
        images = CatalogImage.get_list()
        assert catalog_image in images

    @priority.high
    def test_update_catalog_image_type(self, context):
        step("Create catalog image with image type JAVA")
        test_image = CatalogImage.create(context, image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

        step("Update image type on GO")
        test_image.update(field_name="type", value=TapApplicationType.GO)

        step("Check that the image was updated")
        image = CatalogImage.get(image_id=test_image.id)
        assert test_image == image

    @priority.high
    def test_update_catalog_image_state(self, context):
        step("Create catalog image with image state REQUESTED")
        test_image = CatalogImage.create(context, image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

        step("Update image state on PENDING")
        test_image.update(field_name="state", value=TapEntityState.PENDING)

        step("Check that the image was updated")
        image = CatalogImage.get(image_id=test_image.id)
        assert test_image == image

    @priority.medium
    @pytest.mark.bugs("DPNG-13198 Wrong status code after creating image with existing image id (catalog: images)")
    def test_cannot_create_image_with_existing_image_id(self, context, sample_catalog_image):
        step("Check that it's not possible to create image with existing image id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, CatalogHttpStatus.MSG_KEY_EXISTS,
                                     CatalogImage.create, context, image_id=sample_catalog_image.id,
                                     image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

    @priority.medium
    def test_cannot_get_non_existent_image(self):
        step("Check that it's not possible to get image with non-existent image_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogImage.get, image_id=self.INVALID_ID)

    @priority.low
    @pytest.mark.bugs("DPNG-13199 Wrong status code after send PATCH with wrong prev_value (catalog: images)")
    def test_cannot_update_image_with_wrong_prev_type_value(self, sample_catalog_image):
        step("Check that is't not possible to update image with incorrect prev_value of type")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapApplicationType.NODEJS,
                                                                       TapApplicationType.JAVA)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     sample_catalog_image.update, field_name="type", value=TapApplicationType.GO,
                                     prev_value=TapApplicationType.NODEJS)

    @priority.low
    @pytest.mark.bugs("DPNG-13199 Wrong status code after send PATCH with wrong prev_value (catalog: images)")
    def test_cannot_update_image_with_wrong_prev_state_value(self, sample_catalog_image):
        step("Check that is't not possible to update image with incorrect prev_value of state")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapEntityState.READY,
                                                                       TapEntityState.REQUESTED)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     sample_catalog_image.update, field_name="state", value=TapEntityState.PENDING,
                                     prev_value=TapEntityState.READY)

    @priority.low
    @pytest.mark.bugs("DPNG-13207 Wrong status code after send PATCH with field id (catalog: images)")
    def test_cannot_update_image_id(self, sample_catalog_image):
        step("Check that is't not possible to update image field id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS, catalog_api.update_image,
                                     image_id=sample_catalog_image.id, field_name="id", value=self.INVALID_ID)

    @priority.low
    @pytest.mark.bugs("DPNG-13201 Wrong status code after send PATCH with non-existent state (catalog: images)")
    def test_cannot_update_image_state_to_non_existent_state(self, sample_catalog_image):
        step("Update the image state to nonexistent state")
        wrong_state = "WRONG_STATE"
        expected_message = CatalogHttpStatus.MSG_EVENT_DOES_NOT_EXIST.format(wrong_state)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, sample_catalog_image.update,
                                     field_name="state", value=wrong_state)

    @priority.low
    @pytest.mark.bugs("DPNG-13202 Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: images)")
    def test_cannot_update_image_without_field(self, sample_catalog_image):
        step("Check that it's not possible to update image without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message, catalog_api.update_image,
                                     image_id=sample_catalog_image.id, field_name=None, value=TapEntityState.PENDING)

    @priority.low
    @pytest.mark.bugs("DPNG-13202 Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: images)")
    def test_cannot_update_image_without_value(self, sample_catalog_image):
        step("Check that it's not possible to update image without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message, catalog_api.update_image,
                                     image_id=sample_catalog_image.id, field_name="state", value=None)

    @priority.low
    def test_cannot_update_non_existent_image(self):
        step("Check that it's not possible to update non-existent image")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_image, image_id=self.INVALID_ID, field_name="state",
                                     value=TapEntityState.PENDING)

    @priority.low
    def test_cannot_delete_non_existent_image(self):
        step("Check that it's not possible to delete non-existent image")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_image, image_id=self.INVALID_ID)
