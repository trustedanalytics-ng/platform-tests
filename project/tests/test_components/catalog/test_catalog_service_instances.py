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
from modules.constants import CatalogHttpStatus
from modules.tap_object_model import CatalogInstance, CatalogService, CatalogServiceInstance, CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestCatalogInstancesServices:

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

    def test_1_create_service_instance_in_catalog(self, class_context):
        step("Create service instance in catalog")
        self.__class__.catalog_service_instance = CatalogServiceInstance.create(class_context,
                                                                                service_id=self.catalog_service.id)
        step("Check that instance is on the list of all instances")
        instances = CatalogInstance.get_all()
        assert self.catalog_service_instance in instances
        step("Check that instance is on the list of all service instances")
        service_instances = CatalogServiceInstance.get_all()
        assert self.catalog_service_instance in service_instances
        step("Check that instance is on the list of service instances for the service")
        service_instances = CatalogServiceInstance.get_list_for_service(service_id=self.catalog_service.id)
        assert self.catalog_service_instance in service_instances

    def test_2_update_service_instance(self):
        step("Update name instance by service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_INTERNAL_SERVER_ERROR,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS,
                                     self.catalog_service_instance.update, field_name="name", value="Simple3")

    def test_3_delete_service_instance(self):
        step("Delete instance by service")
        self.catalog_service_instance.delete_instance()
        step("Check that the instance was deleted")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_INSTANCE_DOES_NOT_EXIST,
                                     CatalogServiceInstance.get, service_id=self.catalog_service.id,
                                     instance_id=self.catalog_service_instance.id)

    def test_4_get_instance_for_not_existing_service(self):
        step("Get instance with bad service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, "",
                                     CatalogServiceInstance.get, service_id="badServiceId",
                                     instance_id=self.catalog_service_instance.id)
