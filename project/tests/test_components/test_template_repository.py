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

from modules.constants import HttpStatus, TemplateRepositoryHttpStatus, TapComponent as TAP
from modules.http_calls.kubernetes import k8s_get_configmap
import modules.http_calls.platform.template_repository as template_repository_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import Template
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.template_repository,)
pytestmark = [pytest.mark.components(TAP.template_repository)]


@pytest.mark.usefixtures("open_tunnel")
class TestTemplateRepository:

    @pytest.fixture(scope="function")
    def sample_template(self, context):
        log_fixture("Create sample template")
        return Template.create(context)

    @pytest.fixture(scope="class")
    def generic_application_template_id(self):
        log_fixture("Get generic application template id")
        response = k8s_get_configmap("template-repository")
        return response["data"]["generic-application-template-id"]

    @priority.high
    def test_create_and_delete_template(self, context):
        step("Create template")
        template = Template.create(context)

        step("Check that the template is on the template list")
        templates = Template.get_list()
        assert template in templates

        step("Delete the template")
        template.delete()

        step("Check that the template has been deleted")
        templates = Template.get_list()
        assert template not in templates

    @priority.high
    def test_get_template(self, sample_template):
        step("Get template by id")
        template = Template.get(template_id=sample_template.id)
        assert template == sample_template

    @priority.low
    def test_cannot_create_template_with_existing_id(self, context, sample_template):
        step("Attempt to create a template with existing id causes an error")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, "",
                                     Template.create, context, template_id=sample_template.id)

    @priority.low
    def test_cannot_get_deleted_template(self, sample_template):
        sample_template.delete()
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     TemplateRepositoryHttpStatus.MSG_TEMPLATE_DOES_NOT_EXIST,
                                     Template.get, template_id=sample_template.id)

    @priority.high
    def test_get_parsed_template(self, sample_template):
        step("Check that template is correctly parsed")
        instance_id = "1fef0dfe-16a7-11e6-bde5-00155d3d8812"
        template = Template.get_parsed(template_id=sample_template.id, instance_id=instance_id)
        assert '$' not in str(template.components)

    @priority.high
    def test_cannot_get_parsed_template_with_invalid_instance_id(self, sample_template):
        step("Getting parsed template with invalid instanceId causes an error")
        instance_id = "1fef0d"
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, TemplateRepositoryHttpStatus.MSG_TOO_SHORT_INSTANCE_ID,
                                     Template.get_parsed, template_id=sample_template.id, instance_id=instance_id)

    @priority.medium
    def test_get_parsed_template_for_generic_user_provided_application(self, generic_application_template_id):
        step("Get parsed template for generic user-provided application")
        instance_id = "asdf12343sffs321342dsda"
        other_params = {
            "image": "testImage",
            "hostname": "testHostname",
            "memory_limit": "100M",
        }
        template = Template.get_parsed(template_id=generic_application_template_id, instance_id=instance_id,
                                       optional_params=other_params)
        assert '$' not in str(template.components)

    @priority.low
    def test_get_parsed_template_with_empty_params(self, generic_application_template_id):
        step("Get parsed template for query with empty image and hostname params")
        instance_id = "asdf12343sffs321342dsda"
        other_params = {
            "image": "",
            "hostname": "",
            "memory_limit": "100M",  # mandatory parameter, mandatory numeric format
        }
        template = Template.get_parsed(template_id=generic_application_template_id, instance_id=instance_id,
                                       optional_params=other_params)
        assert '$' not in str(template.components)

    @priority.low
    def test_cannot_get_parsed_template_without_instance_id(self, sample_template):
        step("Getting parsed template without instanceId parameter should cause an error")
        assert_raises_http_exception(TemplateRepositoryHttpStatus.CODE_BAD_REQUEST,
                                     TemplateRepositoryHttpStatus.MSG_UUID_CANNOT_BE_EMPTY,
                                     template_repository_api.get_parsed_template, template_id=sample_template.id,
                                     params={})
