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
import uuid
import pytest
import fixtures.k8s_templates.catalog_service_example as service_body
from modules.tap_logger import step
from modules.markers import incremental
from modules.constants import InstanceFactoryHttpStatus
from modules.tap_object_model.catalog_instance import CatalogInstance
from modules.tap_object_model.catalog_service import CatalogService
from modules.tap_object_model.catalog_template import CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogInstancesMessages:

    INCORRECT_INSTANCE_NAME = "instance!#-{}".format(uuid.uuid4().hex)

    def test_0_prepare_service_for_instance(self, class_context):
        step("Create template in catalog")
        self.__class__.catalog_template = CatalogTemplate.create(class_context, state=CatalogTemplate.STATE_IN_PROGRESS)
        step("Check if template is on list of catalog templates")
        templates = CatalogTemplate.get_list()
        assert self.catalog_template in templates
        step("Create service in catalog")
        self.__class__.catalog_service = CatalogService.create(class_context, template_id=self.catalog_template.id)
        step("Check if service is on list of catalog services")
        services = CatalogService.get_list()
        assert self.catalog_service in services

    def test_1_check_create_instance_with_forbidden_characters(self, class_context):
        step("Check create instance with forbidden characters")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_BAD_REQUEST,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.INCORRECT_INSTANCE_NAME),
                                     CatalogInstance.create, class_context, self.catalog_service.id,
                                     service_body.ng_catalog_instance_bad_name_body, self.INCORRECT_INSTANCE_NAME)

    def test_2_check_create_instance_with_empty_body(self, class_context):
        step("Check create instance with empty body")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_BAD_REQUEST,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_BAD_SERVICEID,
                                     CatalogInstance.create, class_context, self.catalog_service.id, None, None)
