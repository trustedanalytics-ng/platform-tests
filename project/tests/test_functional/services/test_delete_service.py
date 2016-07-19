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

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance
from tests.fixtures.assertions import assert_in_with_retry, assert_raises_http_exception

logged_components = (TAP.service_catalog,)
pytestmark = [components.service_catalog]


@pytest.mark.bugs("DPNG-7140 Internal Server Error (500) on delete service with existing instance.")
@priority.medium
class TestDeleteService:

    @pytest.fixture(autouse=True)
    def create_service_and_instance(self, context, request, test_org, test_space, sample_service):
        step("Create an instance")
        instance = ServiceInstance.api_create(context, test_org.guid, test_space.guid, sample_service.label,
                                              service_plan_guid=sample_service.service_plans[0]["guid"])
        step("Check that service instance is present")
        assert_in_with_retry(instance, ServiceInstance.api_get_list, test_space.guid, sample_service.guid)

    @pytest.mark.parametrize("role", ["auditor", "manager"])
    def test_cannot_delete_service_as_non_space_manager(self, space_users_clients, role, sample_service):
        client = space_users_clients[role]
        step("Attempt to delete service")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_NOT_AUTHORIZED,
                                     sample_service.api_delete, client=client)

    @pytest.mark.parametrize("role", ["developer", "admin"])
    def test_cannot_remove_service_with_instance(self, space_users_clients, role, sample_service):
        client = space_users_clients[role]
        step("Attempt to delete service")
        assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_CANNOT_REMOVE_SERVICE_WITH_INSTANCE,
                                     sample_service.api_delete, client=client)
