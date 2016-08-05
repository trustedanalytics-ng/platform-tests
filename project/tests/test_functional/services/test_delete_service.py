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

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP, ServiceLabels
from modules.markers import priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceInstance, ServiceType
from tests.fixtures.assertions import assert_in_with_retry, assert_raises_http_exception

logged_components = (TAP.service_catalog,)
pytestmark = [pytest.mark.components(TAP.service_catalog)]


@priority.medium
class TestDeleteService:

    @pytest.fixture(scope="class")
    def public_service(self, request, test_space):
        services = ServiceType.api_get_list_from_marketplace(test_space.guid)
        return next(s for s in services if s.label == ServiceLabels.ZOOKEEPER)

    @pytest.mark.parametrize("role", ["developer", "auditor", "manager"])
    def test_cannot_delete_public_service_as_non_admin(self, space_users_clients, role, public_service):
        client = space_users_clients[role]
        step("Attempt to delete public service")
        assert_raises_http_exception(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_USER_NOT_AUTHORIZED_TO_DELETE_SERVICE,
                                     public_service.api_delete, client=client)

    @pytest.mark.parametrize("role", ["developer", "auditor", "manager", "admin"])
    def test_cannot_remove_service_with_instance(self, context, test_org, test_space, space_users_clients, role,
                                                 sample_service):
        step("Create an instance")
        instance = ServiceInstance.api_create(context, test_org.guid, test_space.guid, sample_service.label,
                                              service_plan_guid=sample_service.service_plans[0]["guid"])
        step("Check that service instance is present")
        assert_in_with_retry(instance, ServiceInstance.api_get_list, test_space.guid, sample_service.guid)
        client = space_users_clients[role]
        step("Attempt to delete sample service")
        assert_raises_http_exception(HttpStatus.CODE_INTERNAL_SERVER_ERROR,
                                     HttpStatus.MSG_CANNOT_REMOVE_SERVICE_WITH_INSTANCE,
                                     sample_service.api_delete,
                                     client=client)
