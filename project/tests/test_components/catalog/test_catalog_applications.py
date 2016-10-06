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

from modules.constants import CatalogHttpStatus
from modules.markers import incremental
from modules.tap_logger import step
from modules.tap_object_model.catalog_application import CatalogApplication
from modules.tap_object_model.catalog_image import CatalogImage
from modules.tap_object_model.catalog_template import CatalogTemplate
from tests.fixtures.assertions import assert_raises_http_exception


@incremental
@pytest.mark.usefixtures("open_tunnel")
class TestCatalogApplications:

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

    def test_1_update_application(self):
        step("Update application")
        self.catalog_application.update(field="replication", value=1)
        step("Check application by id")
        application = CatalogApplication.get(self.catalog_application.id)
        assert application.replication == self.catalog_application.replication

    def test_2_delete_application(self):
        step("Delete application")
        self.catalog_application.delete()
        step("Check that the application was deleted")
        applications = CatalogApplication.get_list()
        assert self.catalog_application not in applications

    def test_3_check_application_was_deleted(self):
        step("Check whether application was successfully removed from catalog")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND,
                                     CatalogHttpStatus.MSG_INSTANCE_DOES_NOT_EXIST,
                                     CatalogApplication.get, self.catalog_application.id)
