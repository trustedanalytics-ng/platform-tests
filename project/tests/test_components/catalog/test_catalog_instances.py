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
from modules.tap_object_model import CatalogInstance, CatalogServiceInstance
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
class TestCatalogInstances:

    @pytest.fixture(scope="function")
    def catalog_service_instance(self, class_context, catalog_service):
        log_fixture("Create service instance in catalog")
        return CatalogServiceInstance.create(class_context, service_id=catalog_service.id,
                                             plan_id=catalog_service.plans[0].id)

    @pytest.fixture(scope="function")
    def catalog_instance(self, catalog_service_instance):
        log_fixture("Get service instance from the list of all instances")
        instances = CatalogInstance.get_all()
        instance = next(i for i in instances if i.id == catalog_service_instance.id)
        assert instance is not None, "Service instance was not found on the list of all instances"
        return instance

    @priority.high
    def test_update_instance(self, catalog_instance):
        step("Update the instance")
        catalog_instance.update(field_name="class_id", value="testupdate")
        step("Check that the instance was updated")
        instance = CatalogInstance.get(instance_id=catalog_instance.id)
        # assert instance.classId == catalog_instance.classId
        assert catalog_instance == instance

    @priority.high
    def test_delete_instance(self, catalog_instance):
        step("Delete instance")
        catalog_instance.delete()
        step("Check that the instance was deleted")
        instances = CatalogInstance.get_all()
        assert catalog_instance not in instances

        # TODO this error message should be different
        step("Check that getting the deleted instance returns an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogInstance.get, instance_id=catalog_instance.id)
