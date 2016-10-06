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
from modules.constants import CatalogHttpStatus
import modules.http_calls.platform.catalog as catalog_api
from modules.tap_object_model import CatalogService, CatalogServiceInstance, CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogInstancesMessages:
    # TODO merge with the other file

    INCORRECT_INSTANCE_NAME = "instance!#"

    def test_0_prepare_service_for_instance(self, class_context):
        # TODO change to a fixture
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
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.INCORRECT_INSTANCE_NAME)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogServiceInstance.create, class_context, service_id=self.catalog_service.id,
                                     name=self.INCORRECT_INSTANCE_NAME)

    def test_2_check_create_instance_with_empty_body(self, class_context):
        step("Check create instance with empty body")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, CatalogHttpStatus.MSG_INVALID_JSON,
                                     catalog_api.create_service_instance, service_id=self.catalog_service.id,
                                     name=None, instance_type=None, state=None)
