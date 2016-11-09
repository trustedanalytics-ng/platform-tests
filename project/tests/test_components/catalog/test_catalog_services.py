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

from modules.constants import CatalogHttpStatus, TapComponent as TAP
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogService
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogServices:

    @pytest.fixture(scope="function")
    def catalog_service(self, context, catalog_template):
        log_fixture("Create sample catalog service")
        return CatalogService.create(context, template_id=catalog_template.id)

    @priority.high
    def test_create_and_delete_catalog_service(self, context, catalog_template):
        step("Create catalog service")
        catalog_service = CatalogService.create(context, template_id=catalog_template.id)

        step("Check that the service is on the list of catalog services")
        services = CatalogService.get_list()
        assert catalog_service in services

        step("Delete the service")
        catalog_service.delete()

        step("Check that the service is not on the list of catalog services")
        services = CatalogService.get_list()
        assert catalog_service not in services

        step("Check that getting the deleted service returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogService.get, service_id=catalog_service.id)

    @priority.high
    def test_update_service(self, catalog_service):
        step("Update service")
        catalog_service.update(field_name="description", value="test12")
        step("Check that the service was updated")
        service = CatalogService.get(service_id=catalog_service.id)
        assert service == catalog_service

    @priority.low
    def test_cannot_add_service_with_existing_service_name(self, context, catalog_template, catalog_service):
        step("Add existing service")
        expected_message = CatalogHttpStatus.MSG_SERVICE_EXISTS.format(catalog_service.name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_CONFLICT, expected_message,
                                     CatalogService.create, context, template_id=catalog_template.id,
                                     name=catalog_service.name)
