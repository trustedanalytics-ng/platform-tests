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
from modules.tap_logger import step
from modules.tap_object_model import CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogTemplates:

    INVALID_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"

    @priority.high
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

    @priority.medium
    def test_cannot_create_template_with_template_id(self, context):
        step("Check that it's not possible to create template with template_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, CatalogHttpStatus.MSG_ID_HAS_TO_BE_EMPTY,
                                     CatalogTemplate.create, context, state=TapEntityState.IN_PROGRESS,
                                     template_id=self.INVALID_ID)

    @priority.medium
    def test_cannot_get_template_with_wrong_template_id(self):
        step("Check that it's not possible to get template with wrong template_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogTemplate.get, template_id=self.INVALID_ID)

    @priority.high
    def test_update_catalog_template(self, context):
        step("Create catalog template")
        catalog_template = CatalogTemplate.create(context, state=TapEntityState.IN_PROGRESS)
        step("Update the template")
        catalog_template.update(field_name="state", value=TapEntityState.READY)
        step("Check that the template was updated")
        template = CatalogTemplate.get(template_id=catalog_template.id)
        # assert template.state == catalog_template.state
        assert catalog_template == template

    @priority.low
    @pytest.mark.bugs("DPNG-13025 Wrong status code after send PATCH with wrong prev_value (catalog: templates)")
    def test_cannot_update_catalog_template_with_wrong_prev_state_value(self, catalog_template):
        step("Update the template with incorrect prev_value of state")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapEntityState.UNAVAILABLE,
                                                                       TapEntityState.IN_PROGRESS)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_template.update, field_name="state", value=TapEntityState.READY,
                                     prev_value=TapEntityState.UNAVAILABLE)

    @priority.low
    @pytest.mark.bugs("DPNG-13031 Wrong status code after send PATCH with non-existent state (catalog: templates)")
    def test_cannot_update_catalog_template_state_to_non_existent_state(self, catalog_template):
        step("Update the template state to nonexistent state")
        wrong_state = "WRONG_STATE"
        expected_message = CatalogHttpStatus.MSG_EVENT_DOES_NOT_EXIST.format(wrong_state)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_template.update,
                                     field_name="state", value=wrong_state)

    @priority.low
    @pytest.mark.bugs("DPNG-13033 Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: templates)")
    def test_cannot_update_template_without_field_name(self, catalog_template):
        step("Check that it's not possible to update template without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message, catalog_api.update_template,
                                     template_id=catalog_template.id, field_name=None, value=TapEntityState.IN_PROGRESS)

    @priority.low
    @pytest.mark.bugs("DPNG-13033 Wrong status code and error message after send PATCH without: field, value. "
                      "(catalog: templates)")
    def test_cannot_update_template_without_value(self, catalog_template):
        step("Check that it's not possible to update template without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.MSG_BAD_REQUEST, expected_message, catalog_api.update_template,
                                     template_id=catalog_template.id, field_name="state", value=None)

    @priority.low
    def test_cannot_update_non_existent_template(self):
        step("Check that it's not possible to update non-existent template")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_template, template_id=self.INVALID_ID, field_name="state",
                                     value=TapEntityState.IN_PROGRESS)

    @priority.low
    def test_cannot_delete_non_existent_template(self):
        step("Check that it's not possible to delete non-existent template")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_template, template_id=self.INVALID_ID)
