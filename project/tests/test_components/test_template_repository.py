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

    INSTANCE_ID = "asdf12343sffs321342dsda"

    @pytest.fixture(scope="function")
    def sample_template(self, context):
        log_fixture("Create sample template")
        return Template.create(context)

    @pytest.fixture(scope="class")
    def generic_application_template_id(self):
        log_fixture("Get generic application template id")
        response = k8s_get_configmap("template-repository")
        return response["data"]["generic-application-template-id"]

    @pytest.fixture(scope="class")
    def generic_service_template_id(self):
        log_fixture("Get generic service template id")
        response = k8s_get_configmap("template-repository")
        return response["data"]["generic-service-template-id"]

    @pytest.fixture(scope="class")
    def other_params(self):
        return {
            "image": "testImage",
            "hostname": "testHostname",
            "memory_limit": "100M",
            "cert_hash": "xyz",
        }

    @priority.high
    def test_create_and_delete_template(self, context):
        """
        <b>Description:</b>
        Create, get list and delete template.

        <b>Input data:</b>
        1. Example template body.

        <b>Expected results:</b>
        It is possible to create new template. New template is present on the list of all templates.
        It is possible to delete created template. Deleted template is not present on the list.

        <b>Steps:</b>
        1. Create new template.
        2. Check that new template is present on the list.
        3. Delete new template.
        4. Verify that new template was deleted.
        """
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
        """
        <b>Description:</b>
        Get template.

        <b>Input data:</b>
        1. Sample template id.

        <b>Expected results:</b>
        It is possible to get template.

        <b>Steps:</b>
        1. Create new template.
        2. Get template content.
        """
        step("Get template by id")
        template = Template.get(template_id=sample_template.id)
        assert template == sample_template

    @pytest.mark.bugs("DPNG-13917 No meaningful error message for http status 409 in template-repository")
    @priority.low
    def test_cannot_create_template_with_existing_id(self, context, sample_template):
        """
        <b>Description:</b>
        Checks if creating template with existing id fails.

        <b>Input data:</b>
        1. Sample template id.

        <b>Expected results:</b>
        It is not possible to create template with existing id.

        <b>Steps:</b>
        1. Create new template.
        2. Try to create new template with existing id.
        3. Verify that HTTP response status code is 409 with proper message.
        """
        step("Attempt to create a template with existing id causes an error")
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, "",
                                     Template.create, context, template_id=sample_template.id)

    @pytest.mark.bugs("DPNG-13917 No meaningful error message for http status 409 in template-repository")
    @priority.low
    def test_cannot_create_template_with_generic_app_body(self, context, generic_application_template_id, other_params):
        """
        <b>Description:</b>
        Checks if creating template with generic application template body fails.

        <b>Input data:</b>
        1. Generic application template id.
        2. Parameters.

        <b>Expected results:</b>
        It is not possible to create template with generic application template body.

        <b>Steps:</b>
        1. Get body of generic application template.
        2. Try to create generic application template.
        3. Verify that HTTP response status code is 409 with proper message.
        """
        step("Attempt to create a template with generic application template body causes an error")
        template = Template.get_parsed(template_id=generic_application_template_id, instance_id=self.INSTANCE_ID,
                                       optional_params=other_params)
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, "",
                                     Template.create, context, template_id=template.id,
                                     body=template.components)

    @pytest.mark.bugs("DPNG-13917 No meaningful error message for http status 409 in template-repository")
    @priority.low
    def test_cannot_create_template_with_generic_svc_body(self, context, generic_service_template_id, other_params):
        """
        <b>Description:</b>
        Checks if creating template with generic service template body fails.

        <b>Input data:</b>
        1. Generic service template id.
        2. Parameters.

        <b>Expected results:</b>
        It is not possible to create template with generic service template body.

        <b>Steps:</b>
        1. Get body of generic service template.
        2. Try to create generic service template.
        3. Verify that HTTP response status code is 409 with proper message.
        """
        step("Attempt to create a template with generic service template body causes an error")
        template = Template.get_parsed(template_id=generic_service_template_id, instance_id=self.INSTANCE_ID,
                                       optional_params=other_params)
        assert_raises_http_exception(HttpStatus.CODE_CONFLICT, "",
                                     Template.create, context, template_id=template.id,
                                     body=template.components)

    @priority.low
    def test_cannot_get_deleted_template(self, sample_template):
        """
        <b>Description:</b>
        Checks if getting just deleted template fails.

        <b>Input data:</b>
        1. Sample template id.

        <b>Expected results:</b>
        It is not possible to get template which was removed.

        <b>Steps:</b>
        1. Create sample template.
        2. Delete sample template.
        3. Try to get sample template.
        4. Verify that HTTP response status code is 404 with proper message.
        """
        sample_template.delete()
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     TemplateRepositoryHttpStatus.MSG_TEMPLATE_DOES_NOT_EXIST,
                                     Template.get, template_id=sample_template.id)

    @priority.low
    def test_cannot_delete_deleted_template(self, sample_template):
        """
        <b>Description:</b>
        Checks if deleting just deleted template fails.

        <b>Input data:</b>
        1. Sample template id.

        <b>Expected results:</b>
        It is not possible to delete template which was removed.

        <b>Steps:</b>
        1. Create sample template.
        2. Delete sample template.
        3. Try to delete sample template.
        4. Verify that HTTP response status code is 404 with proper message.
        """
        sample_template.delete()
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     TemplateRepositoryHttpStatus.MSG_NO_TEMPLATE.format(sample_template.id),
                                     sample_template.delete)

    @priority.high
    def test_get_parsed_template(self, sample_template):
        """
        <b>Description:</b>
        Get parsed template.

        <b>Input data:</b>
        1. Sample template id.

        <b>Expected results:</b>
        It is possible to get parsed template.

        <b>Steps:</b>
        1. Create sample template.
        2. Get parsed template.
        3. Verify that sign '$' is not present in template body.
        """
        step("Check that template is correctly parsed")
        template = Template.get_parsed(template_id=sample_template.id, instance_id=self.INSTANCE_ID)
        assert '$' not in str(template.components)

    @priority.high
    def test_cannot_get_parsed_template_with_invalid_instance_id(self, sample_template):
        """
        <b>Description:</b>
        Checks if getting parsed template with invalid instance id fails.

        <b>Input data:</b>
        1. Sample template id.

        <b>Expected results:</b>
        It is not possible to get parsed template with invalid instance id.

        <b>Steps:</b>
        1. Create sample template.
        2. Try to get parsed template with invalid instance id.
        3. Verify that HTTP response status code is 400 with proper message.
        """
        step("Getting parsed template with invalid instanceId causes an error")
        instance_id = "1fef0d"
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST,
                                     TemplateRepositoryHttpStatus.MSG_TOO_SHORT_INSTANCE_ID,
                                     Template.get_parsed, template_id=sample_template.id, instance_id=instance_id)

    @priority.high
    def test_cannot_get_parsed_template_with_non_existing_id(self):
        """
        <b>Description:</b>
        Checks if getting template with non existing template id fails.

        <b>Input data:</b>
        1. Invalid template id.

        <b>Expected results:</b>
        It is not possible to get template with non existing template id.

        <b>Steps:</b>
        1. Try to get template with non existing template id.
        2. Verify that HTTP response status code is 404 with proper message.
        """
        step("Getting parsed template with non existing template id")
        template_id = "asdfasdfasdfasdf"
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND,
                                     TemplateRepositoryHttpStatus.MSG_CANT_FIND_TEMPLATE.format(template_id),
                                     Template.get_parsed, template_id=template_id, instance_id=self.INSTANCE_ID)

    @priority.medium
    def test_get_parsed_template_for_generic_user_provided_application(self, generic_application_template_id,
                                                                       other_params):
        """
        <b>Description:</b>
        Get parsed generic application template for user provided application.

        <b>Input data:</b>
        1. Generic application template id.
        2. Parameters.

        <b>Expected results:</b>
        It is possible to get parsed template with parameters.

        <b>Steps:</b>
        1. Get parsed template for generic application.
        2. Verify that sign '$' is not present in template body.
        3. Verify that parameters have proper values.
        """
        step("Get parsed template for generic user-provided application")
        template = Template.get_parsed(template_id=generic_application_template_id, instance_id=self.INSTANCE_ID,
                                       optional_params=other_params)
        assert '$' not in str(template.components)
        assert other_params['image'] in str(template.components)
        assert other_params['hostname'] in str(template.components)

    @priority.medium
    def test_get_parsed_template_for_services(self, generic_service_template_id, other_params):
        """
        <b>Description:</b>
        Get parsed generic service template for user provided services.

        <b>Input data:</b>
        1. Generic service template id.
        2. Parameters.

        <b>Expected results:</b>
        It is possible to get parsed template with parameters.

        <b>Steps:</b>
        1. Get parsed template for generic services.
        2. Verify that sign '$' is not present in template body.
        3. Verify that parameters have proper values.
        """
        step("Get parsed template for services")
        template = Template.get_parsed(template_id=generic_service_template_id, instance_id=self.INSTANCE_ID,
                                       optional_params=other_params)
        assert '$' not in str(template.components)
        assert other_params['image'] in str(template.components)
        assert other_params['hostname'] in str(template.components)

    @priority.low
    def test_get_parsed_template_with_empty_params(self, generic_application_template_id, generic_service_template_id):
        """
        <b>Description:</b>
        Get parsed templates with empty parameters.

        <b>Input data:</b>
        1. Generic templates ids.
        2. Empty parameters.

        <b>Expected results:</b>
        It is possible to get parsed template with empty parameters.

        <b>Steps:</b>
        1. Get parsed template for generic applications.
        2. Verify that sign '$' is not present in template body.
        3. Get parsed template for generic services.
        4. Verify that sign '$' is not present in template body.
        """
        step("Get parsed template for query with empty image and hostname params")
        other_params = {
            "image": "",
            "hostname": "",
            "memory_limit": "100M",  # mandatory parameter, mandatory numeric format
            "cert_hash": "",
        }
        app_template = Template.get_parsed(template_id=generic_application_template_id, instance_id=self.INSTANCE_ID,
                                           optional_params=other_params)
        assert '$' not in str(app_template.components)
        svc_template = Template.get_parsed(template_id=generic_service_template_id, instance_id=self.INSTANCE_ID,
                                           optional_params=other_params)
        assert '$' not in str(svc_template.components)

    @priority.low
    def test_cannot_get_parsed_template_without_instance_id(self, sample_template):
        """
        <b>Description:</b>
        Checks if getting parsed template without instance id fails.

        <b>Input data:</b>
        1. Sample template id.

        <b>Expected results:</b>
        It is not possible to get parsed template without instance id.

        <b>Steps:</b>
        1. Create sample template.
        2. Try to get parsed template without instance id.
        3. Verify that HTTP response status code is 400 with proper message.
        """
        step("Getting parsed template without instanceId parameter should cause an error")
        assert_raises_http_exception(TemplateRepositoryHttpStatus.CODE_BAD_REQUEST,
                                     TemplateRepositoryHttpStatus.MSG_UUID_CANNOT_BE_EMPTY,
                                     template_repository_api.get_parsed_template, template_id=sample_template.id,
                                     params={})

    @priority.low
    def test_cannot_remove_generic_application_template(self, generic_application_template_id, other_params):
        """
        <b>Description:</b>
        Checks if removing generic application template fails.

        <b>Input data:</b>
        1. Generic application template id.
        2. Parameters.

        <b>Expected results:</b>
        It is not possible to remove generic application template.

        <b>Steps:</b>
        1. Try to delete generic application template.
        2. Verify that HTTP response status code is 403 with proper message.
        3. Verify that generic application template was not deleted.
        """
        step("Removing generic application template should cause an error")
        assert_raises_http_exception(TemplateRepositoryHttpStatus.CODE_FORBIDDEN,
                                     TemplateRepositoryHttpStatus.MSG_REMOVE_TEMPLATE_FORBIDDEN
                                     .format(generic_application_template_id),
                                     template_repository_api.delete_template,
                                     template_id=generic_application_template_id)
        step("Check if template was not deleted")
        template = Template.get_parsed(template_id=generic_application_template_id, instance_id=self.INSTANCE_ID,
                                       optional_params=other_params)
        assert generic_application_template_id == template.id

    @priority.low
    def test_cannot_remove_generic_service_template(self, generic_service_template_id, other_params):
        """
        <b>Description:</b>
        Checks if removing generic service template fails.

        <b>Input data:</b>
        1. Generic service template id.
        2. Parameters.

        <b>Expected results:</b>
        It is not possible to remove generic service template.

        <b>Steps:</b>
        1. Try to delete generic service template.
        2. Verify that HTTP response status code is 403 with proper message.
        3. Verify that generic service template was not deleted.
        """
        step("Removing generic service template should cause an error")
        assert_raises_http_exception(TemplateRepositoryHttpStatus.CODE_FORBIDDEN,
                                     TemplateRepositoryHttpStatus.MSG_REMOVE_TEMPLATE_FORBIDDEN
                                     .format(generic_service_template_id),
                                     template_repository_api.delete_template,
                                     template_id=generic_service_template_id)
        step("Check if template was not deleted")
        template = Template.get_parsed(template_id=generic_service_template_id, instance_id=self.INSTANCE_ID,
                                       optional_params=other_params)
        assert generic_service_template_id == template.id
