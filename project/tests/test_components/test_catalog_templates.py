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
from modules.tap_object_model.catalog_template import CatalogTemplate
from modules.constants import ImageFactoryHttpStatus
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestCatalogTemplates:

    def test_0_create_template_in_catalog(self, class_context):
        step("Create template in catalog")
        self.__class__.catalog_template = CatalogTemplate.create(class_context, state=CatalogTemplate.STATE_IN_PROGRESS)
        step("Check if template is on list of catalog templates")
        templates = CatalogTemplate.get_list()
        assert self.catalog_template in templates

    def test_1_update_catalog_template(self):
        step("Update template")
        self.catalog_template.update(field="state", value=CatalogTemplate.STATE_READY)
        step("Check template by id")
        template = CatalogTemplate.get(self.catalog_template.id)
        assert template.state == self.catalog_template.state

    def test_2_delete_template(self):
        step("Delete template")
        self.catalog_template.delete()
        step("Check that the template was deleted")
        templates = CatalogTemplate.get_list()
        assert self.catalog_template not in templates

    def test_3_check_template_was_deleted(self):
        step("Check whether template was successfully removed from catalog")
        assert_raises_http_exception(ImageFactoryHttpStatus.CODE_NOT_FOUND,
                                     ImageFactoryHttpStatus.MSG_IMAGE_DOES_NOT_EXIST,
                                     CatalogTemplate.get, self.catalog_template.id)
