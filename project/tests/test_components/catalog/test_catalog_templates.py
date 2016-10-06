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
from modules.tap_object_model import CatalogTemplate
from modules.constants import CatalogHttpStatus, TapEntityState
from tests.fixtures.assertions import assert_raises_http_exception


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogTemplates:

    def test_create_and_delete_catalog_template(self, context):
        step("Create catalog template")
        catalog_template = CatalogTemplate.create(context, state=TapEntityState.IN_PROGRESS)

        step("Check that template is on list of catalog templates")
        templates = CatalogTemplate.get_list()
        assert catalog_template in templates

        step("Delete template")
        catalog_template.delete()
        step("Check that the template was deleted")
        templates = CatalogTemplate.get_list()
        assert catalog_template not in templates

        step("Check that getting the deleted application returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogTemplate.get, template_id=catalog_template.id)

    def test_update_catalog_template(self, context):
        step("Create catalog template")
        catalog_template = CatalogTemplate.create(context, state=TapEntityState.IN_PROGRESS)
        step("Update the template")
        catalog_template.update(field_name="state", value=TapEntityState.READY)
        step("Check that the template was updated")
        template = CatalogTemplate.get(template_id=catalog_template.id)
        # assert template.state == catalog_template.state
        assert catalog_template == template
