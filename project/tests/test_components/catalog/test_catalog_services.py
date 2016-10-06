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
from modules.constants import ServiceCatalogHttpStatus
from modules.tap_object_model.catalog_service import CatalogService
from modules.tap_object_model.catalog_template import CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestCatalogService:

    def test_0_create_service(self, class_context):
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

    def test_1_update_service(self):
        step("Update service")
        self.catalog_service.update(field="description", value="test12")
        step("Check service by id")
        service = CatalogService.get(service_id=self.catalog_service.id)
        assert service.description == self.catalog_service.description

    def test_2_add_existing_service(self, class_context):
        step("Add existing service")
        assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_CONFLICT,
                                     ServiceCatalogHttpStatus.MSG_SERVICE_EXISTS.format(self.catalog_service.name),
                                     CatalogService.create, class_context, self.catalog_template.id,
                                     self.catalog_service.name)

    def test_3_delete_service(self):
        step("Delete service")
        self.catalog_service.delete()
        step("Check that the service was deleted")
        services = CatalogService.get_list()
        assert self.catalog_service not in services

    def test_4_check_service_was_deleted(self):
        step("Check whether service was successfully removed from catalog")
        assert_raises_http_exception(ServiceCatalogHttpStatus.CODE_NOT_FOUND,
                                     ServiceCatalogHttpStatus.MSG_SERVICE_DOES_NOT_EXIST,
                                     CatalogService.get, self.catalog_service.id)
