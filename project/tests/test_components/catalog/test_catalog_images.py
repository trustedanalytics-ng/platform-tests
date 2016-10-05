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

from modules.tap_logger import step
from modules.markers import incremental
from modules.tap_object_model.catalog_image import CatalogImage
from modules.constants import ImageFactoryHttpStatus
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestImageFactory:

    def test_0_create_image_in_catalog(self, class_context):
        step("Send application metadata to catalog")
        self.__class__.catalog_image = CatalogImage.create(class_context, image_type=CatalogImage.TYPE_JAVA,
                                                           state=CatalogImage.STATE_PENDING)
        step("Check if image is on list of catalog images")
        images = CatalogImage.get_list()
        assert self.catalog_image in images

    def test_1_update_catalog_image(self):
        step("Update image")
        self.catalog_image.update(field="type", value=CatalogImage.TYPE_GO)
        step("Check image by id")
        image = CatalogImage.get(self.catalog_image.id)
        assert image.state == self.catalog_image.state
        assert image.type == self.catalog_image.type

    def test_2_delete_image(self):
        step("Delete image")
        self.catalog_image.delete()
        step("Check that the image was deleted")
        images = CatalogImage.get_list()
        assert self.catalog_image not in images

    def test_3_check_image_was_deleted(self):
        step("Check whether image was successfully removed from catalog")
        assert_raises_http_exception(ImageFactoryHttpStatus.CODE_NOT_FOUND,
                                     ImageFactoryHttpStatus.MSG_IMAGE_DOES_NOT_EXIST,
                                     CatalogImage.get, self.catalog_image.id)
