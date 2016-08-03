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

from modules.constants import HttpStatus, TemplateRepositoryHttpStatus
from modules.tap_logger import step
from modules.tap_object_model import Template
from modules.markers import incremental
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestTemplateRepository:

    def test_0_create_template(self, class_context):
        step("Create template")
        self.__class__.test_template = Template.create(class_context)
        templates = Template.get_list()
        assert self.test_template in templates

    def test_1_cannot_create_template_with_existing_id(self, class_context):
        step("Create template with existing id")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, "", Template.create, class_context,
                                     template_id=self.test_template.id)

    def test_2_get_template(self):
        step("Get template by id")
        template = Template.get(template_id=self.test_template.id)
        assert template == self.test_template

    def test_3_get_parsed_template(self):
        step("Check if template is correctly parsed")
        template = Template.get_parsed(template_id=self.test_template.id,
                                       service_id="1fef0dfe-16a7-11e6-bde5-00155d3d8812")
        assert '$' not in template.components

    def test_4_cannot_get_parsed_template_with_invalid_service_id(self):
        step("Check service id")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, TemplateRepositoryHttpStatus.MSG_TOO_SHORT_SERVICE_ID,
                                     Template.get_parsed, template_id=self.test_template.id, service_id="1fef0d")

    def test_5_delete_template(self):
        step("Delete template")
        self.test_template.delete()
        step("Check that the template was deleted")
        templates = Template.get_list()
        assert self.test_template not in templates

    def test_6_getting_deleted_template_returns_an_error(self):
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     TemplateRepositoryHttpStatus.MSG_TEMPLATE_DOES_NOT_EXIST,
                                     Template.get, template_id=self.test_template.id)
