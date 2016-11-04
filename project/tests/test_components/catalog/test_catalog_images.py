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
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CatalogImage
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
@pytest.mark.skip(reason="DPNG-12584 Error: Cannot parse ApiServiceInstance list: key PLAN_ID not found!")
class TestCatalogImages:

    @priority.high
    def test_create_and_delete_catalog_image(self, context):
        step("Create catalog image")
        catalog_image = CatalogImage.create(context, image_type=TapApplicationType.JAVA, state=TapEntityState.PENDING)

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

    @priority.high
    def test_update_catalog_image(self, context):
        step("Create catalog image")
        test_image = CatalogImage.create(context, image_type=TapApplicationType.JAVA, state=TapEntityState.PENDING)

        step("Update image")
        test_image.update(field_name="type", value=TapApplicationType.GO)

        step("Check that the image was updated")
        image = CatalogImage.get(image_id=test_image.id)
        assert test_image == image


