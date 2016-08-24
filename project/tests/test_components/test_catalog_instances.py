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


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestCatalogInstances:

    CORRECT_INSTANCE_NAME = "instance-{}".format(uuid.uuid4().hex)
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

    def test_1_create_instance_in_catalog(self, class_context):
        step("Create instance in catalog")
        self.__class__.catalog_instance = CatalogInstance.create(class_context, service_id=self.catalog_service.id,
                                                                 body=service_body.ng_catalog_instance_correct_body,
                                                                 instance_name=self.CORRECT_INSTANCE_NAME)
        step("Check if instance is on list of catalog instances")
        instances = CatalogInstance.get_list()
        assert self.catalog_instance in instances
        step("Create existing instance")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_CONFLICT,
                                     "instance with name: {} already exists!".format(self.CORRECT_INSTANCE_NAME),
                                     CatalogInstance.create, class_context, self.catalog_service.id,
                                     service_body.ng_catalog_instance_correct_body, self.CORRECT_INSTANCE_NAME)

    def test_2_update_instance(self):
        step("Update instance")
        self.catalog_instance.update(field="classId", value="testupdate")
        step("Check instance by id")
        instance = CatalogInstance.get(self.catalog_instance.id)
        assert instance.classId == self.catalog_instance.classId

    def test_3_delete_instance(self):
        step("Delete instance")
        self.catalog_instance.delete()
        step("Check that the instance was deleted")
        instances = CatalogInstance.get_list()
        assert self.catalog_instance not in instances

    def test_4_check_instance_was_deleted(self):
        step("Check whether instance was successfully removed from catalog")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_NOT_FOUND,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_DOES_NOT_EXIST,
                                     CatalogInstance.get, self.catalog_instance.id)

    def test_5_check_create_instance_with_forbidden_characters(self, class_context):
        step("Check create instance with forbidden characters")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_BAD_REQUEST,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(self.INCORRECT_INSTANCE_NAME),
                                     CatalogInstance.create, class_context, self.catalog_service.id,
                                     service_body.ng_catalog_instance_bad_name_body, self.INCORRECT_INSTANCE_NAME)

    def test_6_check_create_instance_with_empty_metadata(self, class_context):
        step("Check create instance with empty metadata")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_BAD_REQUEST, "",
                                     CatalogInstance.create, class_context, self.catalog_service.id,
                                     service_body.ng_catalog_instance_no_metadata_body, self.CORRECT_INSTANCE_NAME)

    def test_7_check_create_instance_with_empty_body(self, class_context):
        step("Check create instance with empty body")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_BAD_REQUEST,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_BAD_SERVICEID,
                                     CatalogInstance.create, class_context, self.catalog_service.id, None, None)

    def test_8_create_instance_in_catalog_by_service(self, class_context):
        step("Create instance in catalog by service")
        self.__class__.catalog_service_instance = CatalogService.create_instance(class_context, service_id=self.catalog_service.id,
                                                                                 body=service_body.ng_catalog_instance_correct_body,
                                                                                 instance_name=self.CORRECT_INSTANCE_NAME)
        step("Check if instance is on list of catalog instances")
        instances = CatalogService.get_instances_list(service_id=self.catalog_service_instance.id)
        assert self.catalog_service_instance in instances
        step("Check if instance is on list of all catalog services instances")
        all_instances = CatalogService.get_all_services_instances_list()
        assert self.catalog_service_instance in all_instances

    def test_9_update_instance_by_service(self):
        step("Update name instance by service")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_INTERNAL_SERVER_ERROR,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS,
                                     self.catalog_service_instance.update, "name", "Simple3")

    def test_10_delete_instance_by_service(self):
        step("Delete instance by service")
        self.catalog_service_instance.delete_instance()
        step("Check that the instance was deleted")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_NOT_FOUND,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_DOES_NOT_EXIST,
                                     CatalogService.get_instance, self.catalog_service_instance.id,
                                     self.catalog_service_instance.instance_id)

    def test_11_get_instance_with_bad_service(self):
        step("Get instance with bad service")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_NOT_FOUND, "",
                                     CatalogService.get_instance, "badServiceId",
                                     self.catalog_service_instance.instance_id)
