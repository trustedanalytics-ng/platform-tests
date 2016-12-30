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
        """
        <b>Description:</b>
        Checks if new image can be created and deleted.

        <b>Input data:</b>
        1. image type: JAVA
        2. image state: REQUESTED

        <b>Expected results:</b>
        Test passes when new image can be created and deleted. According to this, image should be available on the
        list of images after being created and shouldn't be on this list after deletion.

        <b>Steps:</b>
        1. Create image.
        2. Check that the image is on the list of catalog images.
        3. Delete the image.
        4. Check that image is no longer on the list of catalog images.
        """
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
        """
        <b>Description:</b>
        Checks if new image with the given id can be created.

        <b>Input data:</b>
        1. image id: generated test name
        2. image type: JAVA
        3. image state: REQUESTED

        <b>Expected results:</b>
        Test passes when new image can be created. According to this, image should be available on the list of images
        after being created.

        <b>Steps:</b>
        1. Create image with the given id.
        2. Check that the image is on the list of catalog images.
        """
        step("Create image with image_id")
        catalog_image = CatalogImage.create(context, image_id=generate_test_object_name(),
                                            image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)
        step("Check that the image is on the list of catalog images")
        images = CatalogImage.get_list()
        assert catalog_image in images

    @priority.low
    def test_create_image_with_empty_body(self, context):
        """
        <b>Description:</b>
        Checks if there is possibility of creating image with empty body: {}.

        <b>Input data:</b>
        no input data

        <b>Expected results:</b>
        Test passes when image is created. According to this, image should be available on the list of images and
        should has automatically generated id.

        <b>Steps:</b>
        1. Create image with empty body: {}.
        """
        step("Create image with empty_body")
        catalog_image = CatalogImage.create(context)
        step("Check that the image is on the list of catalog images")
        images = CatalogImage.get_list()
        assert catalog_image in images

    @priority.high
    def test_update_catalog_image_type(self, context):
        """
        <b>Description:</b>
        Checks if value of image type can be updated.

        <b>Input data:</b>
        1. image type: JAVA
        2. image state: REQUESTED

        <b>Expected results:</b>
        Test passes when value of image type is updated.

        <b>Steps:</b>
        1. Create catalog image with image type: JAVA, state: REQUESTED.
        2. Update image type on GO.
        3. Check that the image was updated
        """
        step("Create catalog image with image type JAVA")
        test_image = CatalogImage.create(context, image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

        step("Update image type on GO")
        test_image.update(field_name="type", value=TapApplicationType.GO)

        step("Check that the image was updated")
        image = CatalogImage.get(image_id=test_image.id)
        assert test_image == image

    @priority.high
    def test_update_catalog_image_state(self, context):
        """
        <b>Description:</b>
        Checks if value of image state can be updated.

        <b>Input data:</b>
        1. image type: JAVA
        2. image state: REQUESTED

        <b>Expected results:</b>
        Test passes when value of image state is updated.

        <b>Steps:</b>
        1. Create catalog image with image type: JAVA, state: REQUESTED.
        2. Update image state on PENDING.
        3. Check that the image was updated.
        """
        step("Create catalog image with image state REQUESTED")
        test_image = CatalogImage.create(context, image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

        step("Update image state on PENDING")
        test_image.update(field_name="state", value=TapEntityState.PENDING)

        step("Check that the image was updated")
        image = CatalogImage.get(image_id=test_image.id)
        assert test_image == image

    @priority.medium
    def test_cannot_create_image_with_existing_image_id(self, context, sample_catalog_image):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating image with id which already exists.

        <b>Input data:</b>
        1. sample catalog image

        <b>Expected results:</b>
        Test passes when image with id which already exists is not created and status code 409 with error message:
        'Key already exists' is returned.

        <b>Steps:</b>
        1. Create image with id which already exists on platform.
        """
        step("Check that it's not possible to create image with existing image id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, CatalogHttpStatus.MSG_KEY_EXISTS,
                                     CatalogImage.create, context, image_id=sample_catalog_image.id,
                                     image_type=TapApplicationType.JAVA, state=TapEntityState.REQUESTED)

    @priority.medium
    def test_cannot_get_non_existent_image(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of getting image using invalid image id.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when image is not found on the list of images and status code: 404 with message: '100: Key not
        found' is returned.

        <b>Steps:</b>
        1. Get image with incorrect image id.
        """
        step("Check that it's not possible to get image with non-existent image_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogImage.get, image_id=self.INVALID_ID)

    @priority.low
    def test_cannot_update_image_with_wrong_prev_type_value(self, sample_catalog_image):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating image field type giving value type and
        wrong prev_value of type.

        <b>Input data:</b>
        1. sample catalog image type 'JAVA'
        2. new value of type: 'GO'
        3. wrong prev_value of type: 'NODEJS'

        <b>Expected results:</b>
        Test passes when image is not updated and status code 400 with error message: '101: Compare failed
        ([\\\"NODEJS\\\" != \\\"JAVA\\\"]' is returned.

        <b>Steps:</b>
        1. Update image field type giving values: type and wrong prev_value of type.
        """
        step("Check that is't not possible to update image with incorrect prev_value of type")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapApplicationType.NODEJS,
                                                                       TapApplicationType.JAVA)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     sample_catalog_image.update, field_name="type", value=TapApplicationType.GO,
                                     prev_value=TapApplicationType.NODEJS)

    @priority.low
    def test_cannot_update_image_with_wrong_prev_state_value(self, sample_catalog_image):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating image field state giving value state and
        wrong prev_value of state.

        <b>Input data:</b>
        1. sample catalog image type in state 'REQUESTED'
        2. new value of state: 'PENDING'
        3. wrong prev_value of state: 'READY'

        <b>Expected results:</b>
        Test passes when image is not updated and status code 400 with error message: '101: Compare failed
        ([\\\"READY\\\" != \\\"REQUESTED\\\"]' is returned.

        <b>Steps:</b>
        1. Update image field state giving values: state and wrong prev_value of state.
        """
        step("Check that is't not possible to update image with incorrect prev_value of state")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapEntityState.READY,
                                                                       TapEntityState.REQUESTED)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     sample_catalog_image.update, field_name="state", value=TapEntityState.PENDING,
                                     prev_value=TapEntityState.READY)

    @priority.low
    def test_cannot_update_image_id(self, sample_catalog_image):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating image id.

        <b>Input data:</b>
        1. sample catalog image
        2. id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when image is not updated and status code 400 with error message: 'ID and Name fields can not be
        changed!' is returned.

        <b>Steps:</b>
        1. Update image id.
        """
        step("Check that is't not possible to update image field id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS, catalog_api.update_image,
                                     image_id=sample_catalog_image.id, field_name="id", value=self.INVALID_ID)

    @priority.low
    def test_cannot_update_image_state_to_non_existent_state(self, sample_catalog_image):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating image state to not existing state.

        <b>Input data:</b>
        1. sample catalog image
        2. state: 'WRONG_STATE'

        <b>Expected results:</b>
        Test passes when image is not updated and status code 400 with error message: 'event WRONG_STATE does not
        exist' is returned.

        <b>Steps:</b>
        1. Update image state to not existing state.
        """
        step("Update the image state to nonexistent state")
        wrong_state = "WRONG_STATE"
        expected_message = CatalogHttpStatus.MSG_EVENT_DOES_NOT_EXIST.format(wrong_state)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, sample_catalog_image.update,
                                     field_name="state", value=wrong_state)

    @priority.low
    def test_cannot_update_image_without_field(self, sample_catalog_image):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating image omitting argument: field.

        <b>Input data:</b>
        1. sample catalog image

        <b>Expected results:</b>
        Test passes when image is not updated and status code 400 with error message: 'field field is
        empty!' is returned.

        <b>Steps:</b>
        1. Update image omitting argument: field.
        """
        step("Check that it's not possible to update image without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_image,
                                     image_id=sample_catalog_image.id, field_name=None, value=TapEntityState.PENDING)

    @priority.low
    def test_cannot_update_image_without_value(self, sample_catalog_image):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating image omitting argument: value.

        <b>Input data:</b>
        1. sample catalog image

        <b>Expected results:</b>
        Test passes when image is not updated and status code 400 with error message: 'field value is
        empty!' is returned.

        <b>Steps:</b>
        1. Update image omitting argument: value.
        """
        step("Check that it's not possible to update image without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_image,
                                     image_id=sample_catalog_image.id, field_name="state", value=None)

    @priority.low
    def test_cannot_update_non_existent_image(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating image giving invalid image id.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'
        2. image state: 'PENDING'

        <b>Expected results:</b>
        Test passes when image is not updated and status code 404 with error message: '100: Key not found' is returned.

        <b>Steps:</b>
        1. Update image giving invalid image id.
        """
        step("Check that it's not possible to update non-existent image")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_image, image_id=self.INVALID_ID, field_name="state",
                                     value=TapEntityState.PENDING)

    @priority.low
    def test_cannot_delete_non_existent_image(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of deleting not-existing image.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when there is no possibility of deleting image and status code 404 with error message:
        '100: Key not found' is returned.

        <b>Steps:</b>
        1. Delete image giving invalid image id.
        """
        step("Check that it's not possible to delete non-existent image")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_image, image_id=self.INVALID_ID)
