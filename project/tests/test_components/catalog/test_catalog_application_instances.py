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

from modules.constants import CatalogHttpStatus, TapEntityState, TapComponent as TAP
import modules.http_calls.platform.catalog as catalog_api
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import CatalogApplicationInstance
from tests.fixtures.assertions import assert_raises_http_exception


logged_components = (TAP.catalog, )
pytestmark = [pytest.mark.components(TAP.catalog)]


@pytest.mark.usefixtures("open_tunnel")
@pytest.mark.skip(reason="DPNG-12584 Error: Cannot parse ApiServiceInstance list: key PLAN_ID not found!")
class TestCatalogApplicationInstances:

    @priority.high
    def test_create_and_delete_application_instance(self, context, catalog_application):
        step("Create application instance")
        app_instance = CatalogApplicationInstance.create(context, application_id=catalog_application.id)

        step("Check that the instance is on the list of catalog applications")
        instances = CatalogApplicationInstance.get_list_for_application(application_id=catalog_application.id)
        assert app_instance in instances

        step("Delete the application instance")
        app_instance.delete()

        step("Check the application instance is no longer on the list")
        instances = CatalogApplicationInstance.get_all()
        assert app_instance not in instances

        # TODO this error message should be different
        step("Check that getting the deleted application instance returns an error")
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     CatalogApplicationInstance.get, application_id=catalog_application.id,
                                     instance_id=app_instance.id)

    @priority.high
    def test_update_application_instance(self, context, catalog_application):
        step("Create application instance")
        test_instance = CatalogApplicationInstance.create(context, application_id=catalog_application.id)

        step("Update application instance")
        test_instance.update(field_name="state", value=TapEntityState.DEPLOYING)

        step("Check that the application instance was updated")
        instance = CatalogApplicationInstance.get(application_id=catalog_application.id, instance_id=test_instance.id)
        assert test_instance == instance

    @priority.low
    def test_cannot_create_application_instance_without_name(self, context, catalog_application):
        step("Create application instance without name")
        empty_name = ""
        expected_message = CatalogHttpStatus.MSG_INSTANCE_FORBIDDEN_CHARACTERS.format(empty_name)
        assert_raises_http_exception(CatalogHttpStatus.CODE_BAD_REQUEST, expected_message,
                                     CatalogApplicationInstance.create, context, application_id=catalog_application.id,
                                     name=empty_name)

    @priority.low
    def test_cannot_get_application_instances_with_invalid_application_id(self):
        invalid_id = "90982774-09198298"
        step("List instances with invalid application id")
        # TODO this error message should be different
        assert_raises_http_exception(CatalogHttpStatus.CODE_NOT_FOUND, CatalogHttpStatus.MSG_KEY_NOT_FOUND,
                                     catalog_api.get_application_instances, application_id=invalid_id)

