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
from retry import retry

from modules.constants import TapComponent as TAP, Urls, TapApplicationType, TapEntityState, ImageFactoryHttpStatus, HttpStatus
from modules.file_utils import download_file
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Blob, CatalogImage, Image, ImageRepository
from tests.fixtures import assertions
from tests.fixtures.assertions import assert_raises_http_exception

logged_components = (TAP.image_factory, TAP.blob_store, TAP.catalog, TAP.image_repository)
pytestmark = [pytest.mark.components(TAP.image_factory)]


@priority.medium
@pytest.mark.usefixtures("open_tunnel")
class TestImageFactory:

    APP_TYPE = TapApplicationType.NODEJS
    APP_URL = Urls.nodejs_app_url
    INITIAL_IMAGE_STATE = TapEntityState.PENDING
    BLOB_TYPE = "TARGZ"
    catalog_image = None

    @pytest.fixture(scope="function")
    def nodejs_example(self):
        return download_file(url=self.APP_URL, save_file_name="test_blob")

    @pytest.fixture(scope="function")
    def catalog_image(self, context):
        log_fixture("CATALOG: Send application metadata - create an image")
        catalog_image = CatalogImage.create(context, image_type=self.APP_TYPE, state=self.INITIAL_IMAGE_STATE,
                                            blob_type=self.BLOB_TYPE)

        log_fixture("CATALOG: Wait for the image to be in state {}".format(TapEntityState.RUNNING))
        catalog_image.ensure_in_state(TapEntityState.READY)

        log_fixture("CATALOG: Check that the image is on the image list")
        catalog_images = CatalogImage.get_list()
        assert catalog_image in catalog_images
        return catalog_image

    @pytest.fixture(scope="function")
    def blob_store_artifact(self, context, catalog_image, nodejs_example):
        log_fixture("BLOB-STORE: Create an artifact for application")
        created_blob = Blob.create(context, blob_id=catalog_image.id, file_path="@{}".format(nodejs_example))

        log_fixture("BLOB-STORE Check that the blob exists")
        blob = Blob.get(blob_id=catalog_image.id)
        assert blob == created_blob

    @retry(AssertionError, tries=5, delay=2)
    def assert_blob_deleted(self, blob_id):
        assertions.assert_raises_http_exception(ImageFactoryHttpStatus.CODE_NOT_FOUND,
                                                ImageFactoryHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                                Blob.get, blob_id=blob_id)

    @priority.high
    def test_create_image_in_image_factory(self, context, catalog_image):
        step("IMAGE-FACTORY: Create an image")
        Image.create(context, image_id=catalog_image.id)

        step("IMAGE-REPOSITORY: Wait until the image id appears in image-repository")
        assertions.assert_in_with_retry(catalog_image.id, ImageRepository.get_repository_ids)

        step("CATALOG: Check application state")
        catalog_image.ensure_in_state(TapEntityState.READY)

        step("BLOB-STORE: Wait until blob is successfully removed")
        self.assert_blob_deleted(blob_id=catalog_image.id)

    @pytest.mark.parametrize("body", ["invalid body", ""])
    def test_create_image_factory_with_wrong_body(self, class_context, body, catalog_image):
        step("Create image in image-factory with invalid body")
        assert_raises_http_exception(
            HttpStatus.CODE_BAD_REQUEST,
            ImageFactoryHttpStatus.MSG_CREATE_IMAGE_WITH_INVALID_BODY,
            Image.create, class_context, body=body, image_id=catalog_image.id)
