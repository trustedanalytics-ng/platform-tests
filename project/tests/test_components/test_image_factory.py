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

import config
from modules.constants import TapComponent as TAP
from modules.constants.urls import Urls
from modules.file_utils import download_file
from modules.tap_logger import step
from modules.markers import priority, incremental
from modules.tap_object_model.catalog_image import CatalogImage
from modules.tap_object_model.blob import Blob
from modules.tap_object_model.image import Image
from modules.tap_object_model.image_repository import ImageRepository
from modules.constants import ImageFactoryHttpStatus
from tests.fixtures.assertions import assert_raises_http_exception, assert_in_with_retry

logged_components = (TAP.image_factory, TAP.blob_store, TAP.catalog)
pytestmark = [pytest.mark.components(TAP.image_factory)]


@incremental
@priority.medium
@pytest.mark.usefixtures("open_tunnel")
class TestImageFactory:

    NODEJS_APP_NAME = "test_blob"
    NODEJS_APP_TYPE = "NODEJS"
    NODEJS_APP_STATE = "PENDING"
    catalog_image = None

    @pytest.fixture(scope="class")
    def download_nodejs_example(self):
        download_file(Urls.nodejs_app_url, self.NODEJS_APP_NAME)

    def test_0_send_metadata_to_catalog(self, class_context):
        step("Send application metadata to catalog")
        self.__class__.catalog_image = CatalogImage.create(class_context, image_type=self.NODEJS_APP_TYPE,
                                                           state=self.NODEJS_APP_STATE)
        assert self.catalog_image.id is not None

    def test_1_check_metadata_in_catalog_list(self):
        step("Check that metadata are available in catalog - get all images")
        catalog_images = CatalogImage.get_list()
        assert self.catalog_image in catalog_images

    def test_2_check_catalog_metadata(self):
        step("Check that metadata are available in catalog - get image by id")
        image = CatalogImage.get(self.catalog_image.id)
        assert image.state == self.NODEJS_APP_STATE

    def test_3_create_artifact_blob_store(self, class_context, download_nodejs_example):
        step("Create artifact for application in blob-store")
        blob = Blob.create(class_context, self.catalog_image.id, "@/tmp/{}".format(self.NODEJS_APP_NAME))
        assert blob is not None

    def test_4_create_artifact_blob_store_with_existing_id(self, class_context):
        step("Create artifact for application in blob-store once again")
        assert_raises_http_exception(ImageFactoryHttpStatus.CODE_CONFLICT,
                                     ImageFactoryHttpStatus.MSG_BLOB_ID_ALREADY_IN_USE,
                                     Blob.create, class_context, self.catalog_image.id,
                                     "@/tmp/{}".format(self.NODEJS_APP_NAME))

    def test_5_check_blob_exists_in_blob_store(self):
        step("Check whether blob exist in blob-store")
        blob = Blob.get(self.catalog_image.id)
        assert blob is not None

    def test_6_create_image_factory(self, class_context):
        step("Create image in image-factory")
        image = Image.create(class_context, self.catalog_image.id)
        assert image is not None

    def test_7_check_blob_was_deleted(self):
        step("Check whether blob was successfully removed from blob-store")
        assert_raises_http_exception(ImageFactoryHttpStatus.CODE_NOT_FOUND,
                                     ImageFactoryHttpStatus.MSG_BLOB_DOES_NOT_EXIST,
                                     Blob.get, self.catalog_image.id)

    def test_8_check_image_exists(self):
        step("Check whether image exist in image-repository")
        assert_in_with_retry(self.catalog_image.id, ImageRepository.get_repositories)

    def test_9_check_application_state(self):
        step("Check state of application in catalog")
        self.catalog_image.ensure_ready()
        assert self.catalog_image.type == self.NODEJS_APP_TYPE
