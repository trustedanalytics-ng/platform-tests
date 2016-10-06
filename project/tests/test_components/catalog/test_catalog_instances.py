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

from modules.tap_logger import step
from modules.markers import incremental
from modules.constants import CatalogHttpStatus
from modules.tap_object_model import CatalogInstance, CatalogService, CatalogServiceInstance, CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestCatalogInstances:

    CORRECT_INSTANCE_NAME = "instance-{}".format(uuid.uuid4().hex)

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

    def test_1_create_instance_in_catalog(self, class_context):
        step("Create service instance in catalog")
        self.__class__.catalog_instance = CatalogServiceInstance.create(class_context, service_id=self.catalog_service.id)
        step("Check if instance is on list of catalog instances")
        instances = CatalogInstance.get_list()
        assert self.catalog_instance in instances
        step("Create existing instance")
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT,
                                     "instance with name: {} already exists!".format(self.CORRECT_INSTANCE_NAME),
                                     CatalogInstance.create, class_context, service_id=self.catalog_service.id,
                                     name = self.catalog_instance.name)

    def test_2_update_instance(self):
        step("Update instance")
        self.catalog_instance.update(field_name="classId", value="testupdate")
        step("Check instance by id")
        instance = CatalogInstance.get(instance_id=self.catalog_instance.id)
        # assert instance.classId == self.catalog_instance.classId
        assert self.catalog_instance == instance

    def test_3_delete_instance(self):
        step("Delete instance")
        self.catalog_instance.delete()
        step("Check that the instance was deleted")
        instances = CatalogInstance.get_list()
        assert self.catalog_instance not in instances

    def test_4_check_instance_was_deleted(self):
        step("Check whether instance was successfully removed from catalog")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_INSTANCE_DOES_NOT_EXIST,
                                     CatalogInstance.get, instance_id=self.catalog_instance.id)
