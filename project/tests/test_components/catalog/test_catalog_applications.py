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
import modules.http_calls.platform.catalog as catalog_api
from modules.tap_logger import step
from modules.tap_object_model import CatalogApplication
from tests.fixtures.assertions import assert_raises_http_exception


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogApplications:

    def test_create_and_delete_application(self, context, catalog_template, catalog_image):
        step("Create application in catalog")
        catalog_application = CatalogApplication.create(context, template_id=catalog_template.id,
                                                        image_id=catalog_image.id)
        step("Check that application is on the list of catalog applications")
        applications = CatalogApplication.get_list()
        assert catalog_application in applications

        step("Delete the application")
        catalog_application.delete()

        step("Check that the application is not on the list")
        applications = CatalogApplication.get_list()
        assert catalog_application not in applications

        step("Check that getting the deleted application returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogApplication.get, application_id=catalog_application.id)

    def test_update_application(self, context, catalog_template, catalog_image):
        step("Create catalog application")
        catalog_application = CatalogApplication.create(context, template_id=catalog_template.id,
                                                        image_id=catalog_image.id)
        step("Update the application")
        catalog_application.update(field_name="replication", value=2)
        step("Check that application was updated")
        application = CatalogApplication.get(application_id=catalog_application.id)
        assert catalog_application == application

    def test_cannot_get_application_with_invalid_id(self):
        step("Check application with invalid application id")
        invalid_id = "90982774-09198298"
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.get_application, application_id=invalid_id)
