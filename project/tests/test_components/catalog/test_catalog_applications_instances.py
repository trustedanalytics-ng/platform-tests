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

import fixtures.k8s_templates.catalog_service_example as service_body
from modules.constants import InstanceFactoryHttpStatus
from modules.markers import incremental
from modules.tap_logger import step
from modules.tap_object_model.catalog_application import CatalogApplication
from modules.tap_object_model.catalog_image import CatalogImage
from modules.tap_object_model.catalog_template import CatalogTemplate
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestCatalogApplicationsInstances:

    CORRECT_INSTANCE_NAME = generate_test_object_name().replace("_", "-")

    def test_0_create_application(self, class_context):
        step("Create template in catalog")
        self.__class__.catalog_template = CatalogTemplate.create(class_context, state=CatalogTemplate.STATE_IN_PROGRESS)
        step("Check if template is on list of catalog templates")
        templates = CatalogTemplate.get_list()
        assert self.catalog_template in templates
        step("Create image in catalog")
        self.__class__.catalog_image = CatalogImage.create(class_context)
        step("Check if image is on list of catalog images")
        images = CatalogImage.get_list()
        assert self.catalog_image in images
        step("Create application in catalog")
        self.__class__.catalog_application = CatalogApplication.create(class_context, template_id=self.catalog_template.id,
                                                                       image_id=self.catalog_image.id)
        step("Check if application is on list of catalog applications")
        applications = CatalogApplication.get_list()
        assert self.catalog_application in applications

    def test_1_create_application_instance(self, class_context):
        step("Create instance in application")
        self.__class__.application_instance = CatalogApplication.create_instance(class_context,
                                                                        application_id=self.catalog_application.id,
                                                                        body=service_body.ng_catalog_instance_correct_body,
                                                                        instance_name=self.CORRECT_INSTANCE_NAME)
        step("Check if instance is on list of catalog applications")
        application_instances = CatalogApplication.get_instances_list(self.catalog_application.id)
        assert self.application_instance in application_instances

    def test_2_update_application_instance(self):
        step("Update application instance")
        self.application_instance.update_instance(field="state", value="DEPLOYING")
        step("Check application instance by id")
        instance = CatalogApplication.get_instance(self.application_instance.id, self.application_instance.instance_id)
        assert instance.instance_state == self.application_instance.state

    def test_3_delete_application_instance(self):
        step("Delete application instance")
        self.application_instance.delete_application_instance()
        step("Check the application instance was deleted")
        application_instances = CatalogApplication.get_all_services_instances_list()
        assert self.application_instance not in application_instances

    def test_4_check_application_instance_was_deleted(self):
        step("Check whether application instance was successfully removed from catalog")
        assert_raises_http_exception(InstanceFactoryHttpStatus.CODE_NOT_FOUND,
                                     InstanceFactoryHttpStatus.MSG_INSTANCE_DOES_NOT_EXIST,
                                     CatalogApplication.get_instance, self.application_instance.id,
                                     self.application_instance.instance_id)
