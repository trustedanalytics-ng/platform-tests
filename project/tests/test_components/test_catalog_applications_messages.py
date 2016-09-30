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

from modules.constants import HttpStatus
from modules.tap_logger import step
from modules.tap_object_model.catalog_application import CatalogApplication
from modules.tap_object_model.catalog_image import CatalogImage
from modules.tap_object_model.catalog_template import CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception
from modules.test_names import generate_test_object_name


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogApplicationsMessages:

    CORRECT_INSTANCE_NAME = generate_test_object_name().replace("_", "-")
    INVALID_APPLICATION_ID = "90982774-09198298"

    @pytest.mark.bugs("DPNG-11467 Error 400 "Field: Name has incorrect value:" while create catalog application")
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
        self.__class__.catalog_application = CatalogApplication.create(class_context,
                                                                       template_id=self.catalog_template.id,
                                                                       image_id=self.catalog_image.id)
        step("Check if application is on list of catalog applications")
        applications = CatalogApplication.get_list()
        assert self.catalog_application in applications

    @pytest.mark.bugs("DPNG-11467 Error 400 "Field: Name has incorrect value:" while create catalog application")
    def test_1_check_create_application_instance_no_body(self, class_context):
        step("Create instance in application without body")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, "", CatalogApplication.create_instance, class_context,
                                     self.catalog_application.id, "", "")

    def test_2_check_instance_with_invalid_application_id(self):
        step("List instances with invalid application id")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, "", CatalogApplication.get_instances_list, self.INVALID_APPLICATION_ID)

    def test_3_check_application_with_invalid_application_id(self):
        step("Check application with invalid application id")
        assert_raises_http_exception(HttpStatus.CODE_NOT_FOUND, "", CatalogApplication.get, self.INVALID_APPLICATION_ID)
