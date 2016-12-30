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
        """
        <b>Description:</b>
        Checks if new template can be created and deleted.

        <b>Input data:</b>
        no input data

        <b>Expected results:</b>
        Test passes when new template can be created and deleted. According to this, template should be available on
        the list of templates after being created and shouldn't be on this list after deletion.

        <b>Steps:</b>
        1. Create catalog template.
        2. Check that the template is on the list of catalog templates.
        3. Delete the template.
        4. Check that the template is no longer on the list of catalog templates.
        5. Check that getting the deleted template returns an error.
        """
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

        step("Check that getting the deleted template returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogTemplate.get, template_id=catalog_template.id)

    @priority.medium
    def test_cannot_create_template_with_template_id(self, context):
        """
        <b>Description:</b>
        Checks if there is no possibility of creating template giving template id.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when there is no possibility of creating template and status code 400 with error message: 'Id field
        has to be empty!' is returned.

        <b>Steps:</b>
        1. Create template giving template id.
        """
        step("Check that it's not possible to create template with template_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, CatalogHttpStatus.MSG_ID_HAS_TO_BE_EMPTY,
                                     CatalogTemplate.create, context, state=TapEntityState.IN_PROGRESS,
                                     template_id=self.INVALID_ID)

    @priority.medium
    def test_cannot_get_template_with_wrong_template_id(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of getting template using wrong template id.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when template is not returned and status code 404 with error message: '100: Key not found' is
        returned.

        <b>Steps:</b>
        1. Get template using wrong template id.
        """
        step("Check that it's not possible to get template with wrong template_id")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogTemplate.get, template_id=self.INVALID_ID)

    @priority.high
    def test_update_catalog_template(self, context):
        """
        <b>Description:</b>
        Checks if catalog template state can be updated.

        <b>Input data:</b>
        no input data

        <b>Expected results:</b>
        Test passes when value of template state is updated.

        <b>Steps:</b>
        1. Create catalog template in state 'IN PROGRESS'.
        2. Update template state on 'READY'.
        3. Check that the template was updated.
        """
        step("Create catalog template")
        catalog_template = CatalogTemplate.create(context, state=TapEntityState.IN_PROGRESS)
        step("Update the template")
        catalog_template.update(field_name="state", value=TapEntityState.READY)
        step("Check that the template was updated")
        template = CatalogTemplate.get(template_id=catalog_template.id)
        # assert template.state == catalog_template.state
        assert catalog_template == template

    @priority.low
    def test_cannot_update_catalog_template_with_wrong_prev_state_value(self, catalog_template):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating template field state giving value state and wrong prev_value
        of state.

        <b>Input data:</b>
        1. sample catalog template in state 'READY'
        2. new value of state: 'READY'
        3. wrong prev_value of state: 'UNAVAILABLE'

        <b>Expected results:</b>
        Test passes when template is not updated and status code 400 with error message:
        '101: Compare failed ([\\\"UNAVAILABLE\\\" != \\\"IN_PROGRESS\\\"]' is returned.

        <b>Steps:</b>
        1. Update template field state giving values: state and wrong prev_value of state.
        """
        step("Update the template with incorrect prev_value of state")
        expected_message = CatalogHttpStatus.MSG_COMPARE_FAILED.format(TapEntityState.UNAVAILABLE,
                                                                       TapEntityState.IN_PROGRESS)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_template.update, field_name="state", value=TapEntityState.READY,
                                     prev_value=TapEntityState.UNAVAILABLE)

    @priority.low
    def test_cannot_update_catalog_template_state_to_non_existent_state(self, catalog_template):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating template state to not-existing state.

        <b>Input data:</b>
        1. sample catalog template
        2. state: 'WRONG_STATE'

        <b>Expected results:</b>
        Test passes when template is not updated and status code 400 with error message: 'event WRONG_STATE does not
        exist' is returned.

        <b>Steps:</b>
        1. Update template state to not-existing state.
        """
        step("Update the template state to nonexistent state")
        wrong_state = "WRONG_STATE"
        expected_message = CatalogHttpStatus.MSG_EVENT_DOES_NOT_EXIST.format(wrong_state)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_template.update,
                                     field_name="state", value=wrong_state)

    @priority.low
    def test_cannot_update_template_without_field_name(self, catalog_template):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating template omitting argument: field.

        <b>Input data:</b>
        1. sample catalog template

        <b>Expected results:</b>
        Test passes when template is not updated and status code 400 with error message: 'field field is empty!' is
        returned.

        <b>Steps:</b>
        1. Update template omitting argument: field.
        """
        step("Check that it's not possible to update template without field")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("field")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_template,
                                     template_id=catalog_template.id, field_name=None, value=TapEntityState.IN_PROGRESS)

    @priority.low
    def test_cannot_update_template_without_value(self, catalog_template):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating template omitting argument: value.

        <b>Input data:</b>
        1. sample catalog template

        <b>Expected results:</b>
        Test passes when template is not updated and status code 400 with error message: 'field value is empty!' is
        returned.

        <b>Steps:</b>
        1. Update template omitting argument: value.
        """
        step("Check that it's not possible to update template without value")
        expected_message = CatalogHttpStatus.MSG_FIELD_IS_EMPTY.format("value")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message, catalog_api.update_template,
                                     template_id=catalog_template.id, field_name="state", value=None)

    @priority.low
    def test_cannot_update_non_existent_template(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of updating template giving not existing template id.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'
        2. template state: 'IN PROGRESS'

        <b>Expected results:</b>
        Test passes when template is not updated and status code 404 with error message: '100: Key not found' is
        returned.

        <b>Steps:</b>
        1. Update template giving not existing template id.
        """
        step("Check that it's not possible to update non-existent template")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.update_template, template_id=self.INVALID_ID, field_name="state",
                                     value=TapEntityState.IN_PROGRESS)

    @priority.low
    def test_cannot_delete_non_existent_template(self):
        """
        <b>Description:</b>
        Checks if there is no possibility of deleting not existing template.

        <b>Input data:</b>
        1. invalid id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'

        <b>Expected results:</b>
        Test passes when there is no possibility of deleting template and status code 404 with error message: '100:
        Key not found' is returned.

        <b>Steps:</b>
        1. Delete template giving not existing template id.
        """
        step("Check that it's not possible to delete non-existent template")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.delete_template, template_id=self.INVALID_ID)
