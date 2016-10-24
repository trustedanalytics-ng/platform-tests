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
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step, log_fixture
from modules.tap_object_model import CatalogInstance, CatalogServiceInstance
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogServiceInstances:

    @pytest.fixture(scope="class")
    def catalog_service_instance(self, class_context, catalog_service):
        log_fixture("Create sample catalog service instance")
        return CatalogServiceInstance.create(class_context, service_id=catalog_service.id)

    @priority.high
    def test_create_and_delete_service_instance_in_catalog(self, context, catalog_service):
        step("Create service instance in catalog")
        catalog_service_instance = CatalogServiceInstance.create(context, service_id=catalog_service.id)

        step("Check that the service instance is on the list of all instances")
        instances = CatalogInstance.get_all()
        assert catalog_service_instance in instances

        step("Check that the service instance is on the list of all service instances")
        service_instances = CatalogServiceInstance.get_all()
        assert catalog_service_instance in service_instances

        step("Check that the service instance is on the list of service instances for the service")
        service_instances = CatalogServiceInstance.get_list_for_service(service_id=catalog_service.id)
        assert catalog_service_instance in service_instances

        step("Delete the service instance")
        catalog_service_instance.delete()

        step("Check that getting the deleted service instance returns an error")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogServiceInstance.get, service_id=catalog_service.id,
                                     instance_id=catalog_service_instance.id)

    @priority.low
    def test_cannot_update_service_instance_name(self, context, catalog_service_instance):
        step("Check that it's not possible to update name instance by service")
        assert_raises_http_exception(CatalogHttpStatus.CODE_INTERNAL_SERVER_ERROR,
                                     CatalogHttpStatus.MSG_INSTANCE_UNCHANGED_FIELDS,
                                     catalog_api.update_service_instance,
                                     service_id=catalog_service_instance.class_id,
                                     instance_id=catalog_service_instance.id, field_name="name", value="Simple3")
        step("Check that the instance was not updated")
        instance = CatalogServiceInstance.get(service_id=catalog_service_instance.class_id,
                                              instance_id=catalog_service_instance.id)
        assert catalog_service_instance == instance

    @priority.low
    def test_cannot_get_instance_of_not_existing_service(self, context, catalog_service_instance):
        incorrect_service_id = "badServiceId"
        step("Check that getting instance with incorrect service id causes an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogServiceInstance.get, service_id=incorrect_service_id,
                                     instance_id=incorrect_service_id)

    @priority.low
    def test_cannot_create_instance_with_invalid_name(self, context, catalog_service):
        invalid_name = "instance!#"
        step("Try to create instance with name '{}'".format(invalid_name))
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(invalid_name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogServiceInstance.create, context, service_id=catalog_service.id,
                                     name=invalid_name)

    @priority.low
    def test_cannot_create_instance_with_empty_body(self, context, catalog_service):
        step("Check create instance with empty body")
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format("")
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     catalog_api.create_service_instance, service_id=catalog_service.id,
                                     name=None, instance_type=None, state=None)
